# timetemplate.S
# Written 2015 by F Lundevall
# Ported 2024/06 by W Szczerek (from MIPS to RISC-V)
# Copyright abandonded - this file is in the public domain.

#############################################################
# Choose the macro syntax for RARS or DTEK-V board.         #
# The syntax for RARS is probably due to its MIPS heritage. #
#############################################################
###################
# Macros for RARS #
###################
#.macro	PUSH (%reg)
#	addi	sp,sp,-4
#	sw	%reg,0(sp) 
#.end_macro

#.macro	POP (%reg)
#	lw	%reg,0(sp)
#	addi	sp,sp,4
#.end_macro
###################
# Macros for DTEK #
###################
.macro	PUSH reg
	addi sp,sp,-4
	sw \reg,0(sp) 
.endm

.macro	POP reg
	lw	\reg,0(sp)
	addi	sp,sp,4
.endm
#############################################################

	.data
	.align 2
mytime:	.word 	0x5957
timstr:	.asciz 	"text more text lots of text\0"
	.text
	.globl timetemplate, tick, time2string, display_string, delay, hex2asc, hexasc


# Function for displaying a string with a newline at the end	
display_string:	
	li a7,4
	ecall
	li a0, 10
	li a7,11
	ecall
	jr ra
	
timetemplate:
	la	a0, timstr
	jal     display_string
	
	# wait a little
	li	a0, 2		# ms
	jal	delay
	
	# call tick
	la 	a0, mytime
	jal	tick
	
	# call your function time2string
	la	a0, timstr
	la	t0, mytime
	lw	a1, 0(t0)
	jal	time2string
	
	# go back and do it all again
	j	timetemplate

	
# tick: update time pointed to by $a0
tick:	lw	t0, 0(a0)	# get time
	addi	t0, t0, 1	# increase
	andi	t1, t0, 0xf	# check lowest digit
	sltiu	t2, t1, 0xa	# if digit < a, okay
	bnez	t2, tiend
	addi	t0, t0, 0x6	# adjust lowest digit
	
	andi	t1, t0, 0xf0	# check next digit
	sltiu	t2, t1, 0x60	# if digit < 6, okay
	bnez	t2, tiend
	addi	t0, t0, 0xa0	# adjust digit
	
	li	t3, 0xF
	slli	t3, t3, 0x8
	and	t1, t0, t3	# check minute digit
	addi	t3, x0, 0xA
	slli	t3, t3, 0x8
	slt	t2, t1, t3	# if digit < a, okay
	bnez	t2, tiend
	addi	t0, t0, 0x600	# adjust digit - this one's okay, it's lower than 0x7FF 
	
	li	t3, 0xF
	slli	t3, t3, 0xC
	and	t1, t0, t3	# check last digit
	addi	t3, x0, 0x6
	slli	t3, t3, 0xC
	slt	t2, t1, t3	# if digit < 6, okay
	bnez	t2, tiend
	
	li	t3, 0xA
	slli	t3, t3, 0xC
	add	t0, t0, t3	# adjust last digit
tiend:	sw	t0,0(a0)	# save updated result
	jr	ra		# return

#########################################################
# Place for your functions: time2string, hex2asc, delay.#
#########################################################
  # hexmain.S
  # Written 2015-09-04 by F Lundevall
  # Copyright abandonded - this file is in the public domain.

hex2asc:
	li	a0, 17		# test number (from 0 to 15)
	
	addi    sp,sp,-4
	sw      ra,0(sp)
	
	jal	hexasc		# call hexasc
	
	li	a7, 11	# write a0 to stdout
	ecall

	lw      ra,0(sp)
	addi    sp,sp,4
	jr      ra	

  # You can write your own code for hexasc here
  #
hexasc:
	andi	a0,a0,0xF
	PUSH a1
	li	a1,10
	blt	a0,a1,less_than_10
	addi	a0,a0,7	
less_than_10:
	addi	a0,a0,48
	POP a1
	jr	ra
	
delay:
	PUSH a0
	PUSH t0
	PUSH t1
	PUSH t2
	
	mv	t0,a0	# cache a0
	li	t2,4811000	# therehold of for_loop

loop_while:
	ble	t0,zero,end_loop_while
	addi	t0,t0,-1

	li	t1,0	# stand for i
loop_for:
	bge	t1,t2,end_loop_for
	addi	t1,t1,1
	j	loop_for

end_loop_for:
	j	loop_while
end_loop_while:

	POP a0
	POP t0
	POP t1
	POP t2
   	jr ra

time2string:
	PUSH t0
	PUSH a1
	# write the end 0
	li	t0,0x0
	sb	t0,5(a0)
	
# write the first number
	andi	t0,a1,0xF	# get the first number	
	# check if equal to 2
	li	t1,2
	bne	t0,t1,if_not_equal_to_two
	li	t0,0x54		# load T
	sb	t0,4(a0)
	li	t0,0x57		# load W
	sb	t0,5(a0)
	li	t0,0x4f		# load O
	sb	t0,6(a0)
	li	t0,0x0
	sb	t0,7(a0)	# make up for the end 0
	j 	if_equal_to_two

	
	
if_not_equal_to_two:
	PUSH a0
	mv	a0,t0
	PUSH ra
	jal	hexasc
	POP ra
	mv	t0,a0
	POP a0
	sb	t0,4(a0)

if_equal_to_two:
	
	# write the second number
	andi	t0,a1,0xF0
	srli	t0,t0,4
	PUSH a0
	mv	a0,t0
	PUSH ra
	jal	hexasc
	POP ra
	mv	t0,a0
	POP a0
	sb	t0,3(a0)
	
	# write the middle :
	li	t0,0x3A
	sb	t0,2(a0)
	
	# sll a1 to solve the problem that the immediate num is too big
	srli	a1,a1,8
	
	# write the third number
	andi	t0,a1,0xF
	PUSH a0
	mv	a0,t0
	PUSH ra
	jal	hexasc
	POP ra
	mv	t0,a0
	POP a0
	sb	t0,1(a0)
	
	# write the forth number
	andi	t0,a1,0xF0
	srli	t0,t0,4
	PUSH a0
	mv	a0,t0
	PUSH ra
	jal	hexasc
	POP ra
	mv	t0,a0
	POP a0
	sb	t0,0(a0)
	
	POP a1
	POP t0
	
	jr	ra
	
	
	


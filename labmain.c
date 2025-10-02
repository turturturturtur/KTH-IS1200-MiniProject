/* main.c  — DTEK-V: SDRAM + JTAG-UART 图像反相 Demo */

#include <stdint.h>

/* ---- 课程提供的符号 ---- */
extern void print(const char*);
extern void print_dec(unsigned int);
extern void display_string(char*);
extern void time2string(char*,int);
extern void tick(int*);
extern void delay(int);
extern int nextprime(int);
extern void enable_interrupt();

/* ---- JTAG-UART ---- */
#define JTAG_UART_DATA (*(volatile unsigned int*)0x04000040)
#define JTAG_UART_CTRL (*(volatile unsigned int*)0x04000044)

/* ---- SDRAM 通道：PC 侧用 dtekv-upload/download ----
   IN_BASE   : PC 上传输入数据
   OUT_BASE  : CPU 写回输出数据
   LEN_ADDR  : PC 写长度触发，CPU 处理完清零作为 ACK
*/
#define IN_BASE    0x02000000u
#define OUT_BASE   0x02010000u
#define LEN_ADDR   0x0200FFF0u

#define IN_PTR     ((volatile uint8_t*)IN_BASE)
#define OUT_PTR    ((volatile uint8_t*)OUT_BASE)
/* 用宏读写 LEN（32-bit 小端） */
#define LEN_READ()        (*(volatile uint32_t*)LEN_ADDR)
#define LEN_WRITE(val)    do { (*(volatile uint32_t*)LEN_ADDR) = (uint32_t)(val); } while (0)

/* ---- 本地缓冲 ---- */
#define IMG_MAX   (64*1024)          /* 一次最多 64 KiB */
static uint8_t img_buf[IMG_MAX];

/* ---- 你原来的外设与全局 ---- */
int mytime = 0x5957;
int counter = 0;
int prime = 1234567;
int timeoutcount = 0;
int switch_status_previous = 0;
uint32_t n;                 /* PC 写入长度后触发 */
volatile unsigned int* sw_data = (unsigned int*)0x04000010;
volatile unsigned int* sw_dir  = (unsigned int*)0x04000014;
volatile unsigned int* sw_im   = (unsigned int*)0x04000018;
volatile unsigned int* sw_ec   = (unsigned int*)0x0400001C;
char textstring[] = "text, more text, and even more text!";

/* ---- 小工具 ---- */
static inline int jtag_try_recv(uint8_t *out){
  unsigned v = JTAG_UART_DATA;
  if (v & 0x8000) { *out = (uint8_t)(v & 0xFF); return 1; }
  return 0;
}
static inline uint8_t jtag_recv_blocking(void){
  unsigned v; do { v = JTAG_UART_DATA; } while ((v & 0x8000) == 0);
  return (uint8_t)(v & 0xFF);
}
static inline void jtag_send(uint8_t c){
  while ((JTAG_UART_CTRL & 0xFFFF0000) == 0) { /* wait WSPACE */ }
  JTAG_UART_DATA = c;
}
static inline void jtag_recv_exact(uint8_t *buf, int n){
  for (int i=0;i<n;i++) buf[i] = jtag_recv_blocking();
}
static inline void jtag_send_exact(const uint8_t *buf, int n){
  for (int i=0;i<n;i++) jtag_send(buf[i]);
}
/* ---- 调试用：把一个字节以两位十六进制打印 ---- */
static inline void print_hex8(uint8_t b){
  const char *HEX = "0123456789ABCDEF";
  jtag_send(HEX[(b >> 4) & 0xF]);
  jtag_send(HEX[b & 0xF]);
}

/* 打印 label 和 ptr 指向的数据前 k 个字节（十六进制） */
static inline void debug_dump_bytes(const char* label, const volatile uint8_t* ptr, uint32_t n, uint32_t k){
  if (k > n) k = n;
  print(label);
  print(": ");
  for (uint32_t i = 0; i < k; i++){
    print_hex8((uint8_t)ptr[i]);
    jtag_send(' ');
  }
  jtag_send('\n');
}


/* ---- 7 段数码管显示（保留你的实现） ---- */
void set_display(int display_number, int value){
  volatile int *display = (volatile int *)(0x04000050 + 0x10*display_number);
  int m[10] = {0x40,0x79,0x24,0x30,0x19,0x12,0x02,0x78,0x00,0x10};
  *display = m[value];
}
int get_sw(void){ volatile int* p=(volatile int*)0x04000010; return (*p)&0x03ff; }
int get_btn(void){ volatile int* p=(volatile int*)0x040000d0; return (*p)&0x1; }

/* ---- 中断（原样保留） ---- */
void handle_interrupt(unsigned cause){
  int hour,minute,second;
  int supported_method_num = 3;
  volatile int *timer = (volatile int *)0x04000020;
  int switch_status_now = get_sw();
  int sw_exit = switch_status_now & 0x1;
  int sw_confirm = switch_status_now & 0x2;
  int sw_method = (switch_status_now>>2);

  if (timer[0] & 0x1){
    timer[0] = 0x1;
    timer[2] = 0xc6bf;
    timer[3] = 0x002d;
    timer[1] = 0x7;
    timeoutcount++;
    if (timeoutcount % 10 == 0){ tick(&mytime); counter++; }
  }
  if (cause==17){
    print("[Debug]sw trigger!\n");
      /* ---- SDRAM 触发通道 ---- */

    if (n != 0 && sw_method!=0){
      /* 简单健壮性：限制单次处理上限 */
      if (n > IMG_MAX) n = IMG_MAX;

      /* ---- 打印输入长度 + 输入前 16 字节（直接从 SDRAM 读）---- */
      print("LEN(read)="); print_dec(n); print("\n");
      debug_dump_bytes("IN[0:16]", IN_PTR, n, 16);

      /* 1) 从 IN_BASE 读取到本地缓冲 */
      for (uint32_t i=0;i<n;i++) img_buf[i] = IN_PTR[i];

      /* 2) 逐字节取反 */
      switch(sw_method){
        case 1: // Invert
          for (uint32_t i = 0; i < n; i++) {
              img_buf[i] = (uint8_t)~img_buf[i];
          }
          break;

        case 2: // Brighten: add 50, clamp to 255
          for (uint32_t i = 0; i < n; i++) {
              uint16_t val = (uint16_t)img_buf[i] + 50;
              img_buf[i] = (val > 255) ? 255 : (uint8_t)val;
          }
          break;

        case 3: // Darken: subtract 50, clamp to 0
          for (uint32_t i = 0; i < n; i++) {
              int16_t val = (int16_t)img_buf[i] - 50;
              img_buf[i] = (val < 0) ? 0 : (uint8_t)val;
          }
          break;
      }


      /* 3) 回写 OUT_BASE */
      for (uint32_t i=0;i<n;i++) OUT_PTR[i] = img_buf[i];
      debug_dump_bytes("OUT[0:16]", OUT_PTR, n, 16);



      // /* ---- JTAG-UART 二进制协议（保留）---- */
      // uint8_t cmd;
      // if (jtag_try_recv(&cmd)){
      //   if (cmd == 'I'){
      //     uint16_t sz = 0;
      //     sz  = jtag_recv_blocking();
      //     sz |= ((uint16_t)jtag_recv_blocking() << 8);
      //     if (sz > IMG_MAX) sz = IMG_MAX;

      //     jtag_recv_exact(img_buf, sz);
      //     for (int i=0;i<sz;i++) img_buf[i] = (uint8_t)~img_buf[i];
      //     jtag_send((uint8_t)(sz & 0xFF));
      //     jtag_send((uint8_t)(sz >> 8));
      //     jtag_send_exact(img_buf, sz);
      //   }
      // }

      /* 空转给外设时间；避免过度忙等可按需加小延迟 */
      __asm__ volatile("nop");
    }
      *sw_ec = 0xFFFFFFFF;
      delay(1);
  }
  if(sw_method<=supported_method_num){
    set_display(5,(sw_method/10)); set_display(4,sw_method%10);
  }else{
    set_display(5,9); set_display(4,9);
  }

  minute = (counter%3600)/60;
  set_display(3,(minute%100)/10); set_display(2,minute%10);
  second = (counter%60);
  set_display(1,(second%100)/10); set_display(0,second%10);
}

/* ---- 初始化（原样保留） ---- */
void labinit(void){
  volatile int* timer = (volatile int *)0x04000020;
  timer[1] = (1<<3);
  timer[2] = 0xc6bf;
  timer[3] = 0x002d;
  timer[1] = 0x7;

  *sw_dir = 0x00000000;
  *sw_ec  = 0xFFFFFFFF;
  *sw_im = 0x000003FF;

  switch_status_previous = (*sw_data) & 0x2;
  enable_interrupt();
}

/* ---- 主程序 ---- */
int main(void){
  labinit();

  print("================================================\n");
  print("JTAG-UART / SDRAM image invert ready.\n");
  print("PC can either:\n");
  print("  (A) JTAG-UART: send 'I' + <len_lo><len_hi> + payload; board echoes back inverted.\n");
  print("  (B) SDRAM: dtekv-upload img -> 0x02000000; len(LE32)->0x0200FFF0;\n");
  print("             board writes inverted to 0x02010000 and clears len to 0.\n");
  print("================================================\n");
  n = LEN_READ();                 /* PC 写入长度后触发 */
  /* 4) 清零 ACK */
  LEN_WRITE(0);
}

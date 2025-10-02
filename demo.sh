python gen_img.py

# 上传输入
dtekv-upload img.bin 0x02000000

# 写长度（例：1024 = 0x00000400，小端）
# 方式1：printf 到文件（最简单）
printf '\x00\x04\x00\x00' > len.bin     # 1024 的 LE32：00 04 00 00
ls -l len.bin                           # 必须是 4 字节
xxd len.bin
dtekv-upload len.bin 0x0200FFF0


# You need to wait until the main process is done!

dtekv-run main.bin 

# 下载输出（这步不要 Ctrl+C！等它结束）
dtekv-download out.bin 0x02010000 1024

# 验证文件
ls -lh out.bin
hexdump -C out.bin | head

# python viz_img.py --save output_img.png
python viz_img.py
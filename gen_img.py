# gen_img.py
# 生成一个假的 img.bin 文件，带有棋盘格+渐变图案
# 默认大小 1024 字节 (32x32)

import numpy as np

def gen_img(filename="img.bin", size=1024):
    # 假设是方形图像
    side = int(size ** 0.5)
    if side * side != size:
        raise ValueError("size 必须是平方数，比如 1024=32x32, 4096=64x64")

    img = np.zeros((side, side), dtype=np.uint8)

    # 生成棋盘格：奇偶行列交替 + 渐变叠加
    for y in range(side):
        for x in range(side):
            base = ((x // 4 + y // 4) % 2) * 128  # 棋盘格
            grad = int(127 * (x / side))          # 水平渐变
            val = (base + grad) % 256
            img[y, x] = val

    # 写文件
    with open(filename, "wb") as f:
        f.write(img.tobytes())

    print(f"Generated {filename} ({size} bytes, {side}x{side})")

if __name__ == "__main__":
    gen_img("img.bin", 1024)   # 默认 32x32
    # gen_img("img4096.bin", 4096)  # 你也可以生成 64x64

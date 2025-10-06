# viz_vga_img.py
# 可视化一个 320x240, 8-bit RRRGGGBB 格式的原始图像文件

import numpy as np
import matplotlib.pyplot as plt
import argparse

WIDTH = 320
HEIGHT = 240

def decode_rgb332_to_rgb888(byte_val):
    """将一个 RRRGGGBB 字节解码为 (R, G, B) 元组 (0-255)"""
    # 提取 R, G, B 分量
    r_3bit = (byte_val >> 5) & 0b111  # 提取高3位
    g_3bit = (byte_val >> 2) & 0b111  # 提取中3位
    b_2bit = byte_val & 0b011          # 提取低2位

    # 将分量从低位深扩展到 8-bit (0-255)
    # 简单的做法是左移，但更好的做法是按比例扩展
    r_8bit = int((r_3bit / 7.0) * 255)
    g_8bit = int((g_3bit / 7.0) * 255)
    b_8bit = int((b_2bit / 3.0) * 255)
    
    return (r_8bit, g_8bit, b_8bit)

def visualize(input_filename, save_filename=None):
    expected_size = WIDTH * HEIGHT
    
    try:
        with open(input_filename, "rb") as f:
            raw_data = f.read()
    except FileNotFoundError:
        print(f"Error: File '{input_filename}' not found.")
        return

    if len(raw_data) != expected_size:
        print(f"Error: File size is {len(raw_data)}, but expected {expected_size}.")
        return

    # 创建一个用于显示的 3D numpy 数组 (H, W, 3 for RGB)
    display_img = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

    # 逐字节解码并填充到显示数组
    for i in range(expected_size):
        y = i // WIDTH
        x = i % WIDTH
        
        byte_val = raw_data[i]
        rgb_tuple = decode_rgb332_to_rgb888(byte_val)
        display_img[y, x] = rgb_tuple

    # 使用 matplotlib 显示图像
    plt.imshow(display_img)
    plt.title(f"Visualization of {input_filename}")
    plt.axis('off')  # 关闭坐标轴

    if save_filename:
        plt.savefig(save_filename)
        print(f"Image saved to {save_filename}")
        
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualize a 320x240 8-bit RRRGGGBB raw image.")
    parser.add_argument("input_file", help="The raw image file to display (e.g., vga_out.bin).")
    parser.add_argument("--save", help="Optional: Save the visualization to a PNG file.")
    
    args = parser.parse_args()
    
    visualize(args.input_file, args.save)
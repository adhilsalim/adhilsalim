import sys
from PIL import Image

def create_image_with_heart(x, y):
    width, height = 1250, 650  
    background_color = (0, 0, 0)  
    img = Image.new("RGBA", (width, height), background_color)

    heart_image = Image.open("images/heart.png")
    heart_image = heart_image.convert("RGBA")
    heart_image.thumbnail((50, 50), Image.LANCZOS)

    if 0 <= x <= 600:
        x_position = x
    elif -600 <= x < 0:
        x_position = 600 + x
    else:
        x_position = 600

    if 0 <= y <= 300:
        y_position = 300 - y
    elif -300 <= y < 0:
        y_position = 300 + y
    else:
        y_position = 300

    print(f"x axis of heart: {x_position}")
    print(f"y axis of heart: {y_position}")

    img.paste(heart_image, (x_position, y_position), heart_image)

    img.save("github_banner_heart.png")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_banner.py <X-coordinate> <Y-coordinate>")
        sys.exit(1)

    x_input = int(sys.argv[1])
    y_input = int(sys.argv[2])

    create_image_with_heart(x_input, y_input)
    print("Image created and saved as github_banner_heart.png")

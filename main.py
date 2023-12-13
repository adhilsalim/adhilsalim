from PIL import Image

def create_image_with_heart(x, y):
    # Create a black background image
    width, height = 1250, 650  # You can adjust the size as needed
    background_color = (0, 0, 0)  # Black
    img = Image.new("RGBA", (width, height), background_color)

    # Load the heart image and resize it to fit within the background
    heart_image = Image.open("images/heart.png")
    heart_image = heart_image.convert("RGBA")
    heart_image.thumbnail((50, 50), Image.LANCZOS)

    # Calculate the position to paste the heart image
    # x_position = (width - heart_image.width) // 2
    # y_position = (height - heart_image.height) // 2

    # Create a mask from the alpha channel of the heart image
    r, g, b, a = heart_image.split()
    mask = a

    if (x >= 0 and x <= 600):
        x = x+600
    elif (x < 0 and x>=-600):
        x = (600-(x*-1))
    else:
        x = 600
    
    if (y >= 0 and y <= 300):
        y = 300-y
    elif (y < 0 and y>=-300):
        y = (y*-1)+300
    else:
        y = 300
    
    # # Adjust x within the range [0, 600]
    # x = min(max(x, 0), 600) + 600 if x < 0 else min(x, 600)

    # # Adjust y within the range [0, 300]
    # y = min(max(y, 0), 300) + 300 if y < 0 else min(y, 300)

    print(f"x axis of heart: {x}")
    print(f"y axis of heart: {y}")

    # Paste the resized heart image onto the black background using the mask
    img.paste(heart_image, (x, y), mask)

    # Save the final image
    img.save("img.png")

if __name__ == "__main__":
    # Get user input for X and Y coordinates
    x_input = int(input("Enter the X coordinate: "))
    y_input = int(input("Enter the Y coordinate: "))

    create_image_with_heart(x_input, y_input)

    print("Image created and saved as img.png.")

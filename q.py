from PIL import Image, ImageDraw, ImageFont

# Define the text
text = "go tell"

# Load a font
font_size = 200
font = ImageFont.truetype("./virtual-regular.ttf", font_size)

# Calculate the text's bounding box
bbox = font.getbbox(text)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]

# Create an image with the bounding box size
image = Image.new("RGB", (text_width, text_height +bbox[1] ), color="white")

# Draw the text on the image
draw = ImageDraw.Draw(image)
draw.text((0, 0), text, font=font, fill="black")

# Save or show the image
image.show()  # Display the image
# image.save("text_bounding_box.png")  # Save the image

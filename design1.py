import argparse
from PIL import Image, ImageDraw, ImageFont
import json
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk import pos_tag
import nltk
import re

# Uncomment below lines after first run
nltk.download("punkt")
nltk.download("punkt_tab")
nltk.download("averaged_perceptron_tagger")
nltk.download("averaged_perceptron_tagger_eng")
nltk.download("stopwords")

DEFAULT_HEIGHT = 22
LONG_HEIGHT = 34
DEFAULT_WIDTH = 31
CENTER_WIDTH = 38


def emphasize_split(phrase):
    # Tokenize the phrase
    words = word_tokenize(phrase)

    # Tag parts of speech
    pos_tags = pos_tag(words)
    print("pos_tags", pos_tags)
    # Define emphasis words (e.g., adjectives, nouns)
    emphasis_tags = {"RB", "RBS", "JJ", "JJS", "NN", "NNS"}

    # Find emphasis points
    emphasis_points = [
        i for i, (word, tag) in enumerate(pos_tags) if tag in emphasis_tags
    ]

    # Decide split point (heuristically: last emphasis point in the first half)
    split_index = (
        emphasis_points[len(emphasis_points) // 2]
        if emphasis_points
        else len(words) // 2
    )

    # Split the phrase
    part1 = " ".join(words[: split_index + 1])
    part2 = " ".join(words[split_index + 1 :])

    return part1, part2


def load_config():
    with open("./config.json", "rt") as infile:
        config = json.loads(infile.read())
        return config


def draw_wrapped_centered_text(
    text, font: ImageFont.ImageFont, max_width, start_y=0, fill="black", bg="white"
):
    """
    Draws wrapped text on an image and centers each line horizontally.

    Parameters:
        image (PIL.Image.Image): The image to draw on.
        text (str): The text to draw.
        font (PIL.ImageFont.FreeTypeFont): The font to use.
        max_width (int): The maximum width for wrapping text.
        start_y (int): The y-coordinate to start drawing text.
        fill (str or tuple): The fill color for the text.
    """
    words = text.split()
    lines = []
    current_line = ""

    # Wrap text manually
    for word in words:
        test_line = f"{current_line} {word}".strip()
        line_width = font.getlength(test_line)
        if line_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    # Calculate line height
    font_bbox = font.getbbox("A")
    line_height = font_bbox[3] - font_bbox[1]
    line_extra = font_bbox[1]
    image = Image.new("RGB", (max_width, line_extra + line_height * len(lines)), bg)
    draw = ImageDraw.Draw(image)

    # Draw each line centered horizontally
    image_width = image.width
    y = start_y
    for line in lines:
        line_width = font.getlength(line)
        x = (image_width - line_width) // 2  # Center the line horizontally
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height

    return crop_whitespace(image)


def crop_whitespace(image, bg_color=(255, 255, 255)):
    """
    Crops white (or specified background color) spaces from the top and bottom of an image.

    Parameters:
        image (PIL.Image.Image): The input image.
        bg_color (tuple): The background color to be treated as whitespace (default is white).

    Returns:
        PIL.Image.Image: The cropped image.
    """
    # Convert image to RGB mode if not already
    image = image.convert("RGB")

    # Load pixel data
    pixels = image.load()
    width, height = image.size

    # Find the first and last rows that are not entirely bg_color
    top = 0
    bottom = height - 1

    def is_row_whitespace(y):
        for x in range(width):
            if pixels[x, y] != bg_color:
                return False
        return True

    # Scan from top to find the first non-whitespace row
    while top < height and is_row_whitespace(top):
        top += 1

    # Scan from bottom to find the first non-whitespace row
    while bottom > top and is_row_whitespace(bottom):
        bottom -= 1

    # Crop and return the image
    return image.crop((0, top, width, bottom + 1))


def combine_images(images: list[Image.Image]):
    """
    docstring
    """
    total_height = sum(i.size[1] for i in images) + 10
    base = Image.new("RGB", (images[0].size[0], total_height), "white")
    y = 5
    for im in images:
        base.paste(im, (0, y))
        y += im.height

    return base


def draw_title(title: str, config: dict, canvas: Image.Image):
    match = re.match(r"^\s*(\d+)(.+)", title.strip())
    text = None
    number = None
    if match:
        number = match.group(1)
        text = match.group(2)
    else:
        text = title.strip()

    str1, str2 = emphasize_split(text)
    print("str1", str1)
    print("str2", str2)

    number_font = ImageFont.truetype(config["font1_path"], config["number_size"])
    str1_font = ImageFont.truetype(config["font2_path"], config["text1_size"])
    str2_font = ImageFont.truetype(config["font1_path"], config["text2_size"])

    to_width = int((CENTER_WIDTH / 100) * config["width"])

    titles_images = []
    if number:
        number_image = draw_text_to_width(
            number, number_font, to_width, fill=tuple(config["color_number"])
        )
        titles_images.append(number_image)

    str1_img = draw_wrapped_centered_text(
        str1, str1_font, to_width, fill=tuple(config["color_text1"])
    )
    str2_img = draw_wrapped_centered_text(
        str2, str2_font, to_width, fill=tuple(config["color_text2"])
    )
    titles_images.append(str1_img)
    titles_images.append(str2_img)

    combined = combine_images(titles_images)

    x = int((config["width"] - combined.width) / 2)
    y = int((config["height"] - combined.height) / 2)
    canvas.paste(combined, (x, y))

    return canvas, combined


def draw_text_to_width(text, font, to_width, fill, bg="white"):
    left, top, right, bottom = font.getbbox(text)
    width = right - left
    height = bottom
    img_num = Image.new(
        "RGB",
        (to_width, height),
        color=bg,
    )
    draw = ImageDraw.Draw(img_num)
    x = (to_width - width) / 2
    draw.text((x, 0), text, font=font, fill=fill)

    cropped_text = crop_whitespace(img_num)
    return cropped_text


def compose_image(images: list, title: str):
    config = load_config()
    canvas = Image.new("RGB", size=(config["width"], config["height"]), color="white")
    canvas, title_image = draw_title(title, config, canvas)

    # image layouting is from Top to Bottom, Left to Right
    for ix, img in enumerate(images):
        if ix == 0:
            img_width = (DEFAULT_WIDTH / 100) * config["width"]
            img_height = (DEFAULT_HEIGHT / 100) * config["height"]
            pos_x = 0
            pos_y = 0
        if ix == 1:
            img_width = (DEFAULT_WIDTH / 100) * config["width"]
            img_height = (DEFAULT_HEIGHT / 100) * config["height"]
            pos_x = 0
            pos_y = img_height
        if ix == 2:
            img_width = (DEFAULT_WIDTH / 100) * config["width"]
            img_height = (LONG_HEIGHT / 100) * config["height"]
            pos_x = 0
            pos_y = 2 * (DEFAULT_HEIGHT / 100) * config["height"]
        if ix == 3:
            img_width = (DEFAULT_WIDTH / 100) * config["width"]
            img_height = (DEFAULT_HEIGHT / 100) * config["height"]
            pos_x = 0
            pos_y = (2 * (DEFAULT_HEIGHT / 100) * config["height"]) + (
                (LONG_HEIGHT / 100) * config["height"]
            )

        if ix == 4:
            img_width = (CENTER_WIDTH / 100) * config["width"]
            img_height = (DEFAULT_HEIGHT / 100) * config["height"]
            pos_x = (DEFAULT_WIDTH / 100) * config["width"]
            pos_y = 0

        if ix == 5:
            img_width = (CENTER_WIDTH / 100) * config["width"]
            # img_height =    ((DEFAULT_HEIGHT / 100) * config["height"]) / 2
            img_height = (
                config["height"]
                - 2 * (DEFAULT_HEIGHT * config["height"] / 100)
                - title_image.height
            ) // 2

            pos_x = (DEFAULT_WIDTH / 100) * config["width"]
            pos_y = (DEFAULT_HEIGHT / 100) * config["height"]

        if ix == 6:
            img_width = (CENTER_WIDTH / 100) * config["width"]
            # img_height = ((DEFAULT_HEIGHT / 100) * config["height"]) / 2
            img_height = (
                config["height"]
                - 2 * (DEFAULT_HEIGHT * config["height"] / 100)
                - title_image.height
            ) // 2

            pos_x = (DEFAULT_WIDTH / 100) * config["width"]
            pos_y = (
                config["height"]
                - (DEFAULT_HEIGHT / 100) * config["height"]
                - img_height
            )

        if ix == 7:
            img_width = (CENTER_WIDTH / 100) * config["width"]
            img_height = (DEFAULT_HEIGHT / 100) * config["height"]
            pos_x = (DEFAULT_WIDTH / 100) * config["width"]
            pos_y = config["height"] - (DEFAULT_HEIGHT / 100) * config["height"]

        if ix == 8:
            img_width = (DEFAULT_WIDTH / 100) * config["width"]
            img_height = (DEFAULT_HEIGHT / 100) * config["height"]
            pos_x = config["width"] - img_width
            pos_y = 0

        if ix == 9:
            img_width = (DEFAULT_WIDTH / 100) * config["width"]
            img_height = (LONG_HEIGHT / 100) * config["height"]
            pos_x = config["width"] - img_width
            pos_y = (DEFAULT_HEIGHT / 100) * config["height"]

        if ix == 10:
            img_width = (DEFAULT_WIDTH / 100) * config["width"]
            img_height = (DEFAULT_HEIGHT / 100) * config["height"]
            pos_x = config["width"] - img_width
            pos_y = config["height"] - 2 * img_height

        if ix == 11:
            img_width = (DEFAULT_WIDTH / 100) * config["width"]
            img_height = (DEFAULT_HEIGHT / 100) * config["height"]
            pos_x = config["width"] - img_width
            pos_y = config["height"] - img_height

        new_img = Image.open(img).resize((int(img_width), int(img_height)))
        draw = ImageDraw.Draw(new_img)
        draw.rectangle(
            [(0, 0), (new_img.width - 1, new_img.height - 1)], outline="white", width=2
        )
        canvas.paste(new_img, (int(pos_x), int(pos_y)))
        canvas.save("./output.png")


def main():
    images = [
        "C:\dev\pillow-benj\source_img\download (3).jpg",
        "C:\dev\pillow-benj\source_img\download (4).jpg",
        "C:\dev\pillow-benj\source_img\download (5).jpg",
        "C:\dev\pillow-benj\source_img\download (6).jpg",
        "C:\dev\pillow-benj\source_img\download (7).jpg",
        "C:\dev\pillow-benj\source_img\download (8).jpg",
        "C:\dev\pillow-benj\source_img\download (9).jpg",
        "C:\dev\pillow-benj\source_img\images (1).jpg",
        "C:\dev\pillow-benj\source_img\images (2).jpg",
        "C:\dev\pillow-benj\source_img\images (3).jpg",
        "C:\dev\pillow-benj\source_img\images (4).jpg",
        "C:\dev\pillow-benj\source_img\images.jpg",
    ]

    compose_image(images, "25 best places to visit in London")


if __name__ == "__main__":
    main()

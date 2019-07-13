import pytesseract
import argparse
from PIL import Image
from subprocess import check_output


def resolve(image_path):
    print("Resampling the Image")
    check_output(
        ['convert', image_path, '-resample', '600', image_path])
    return pytesseract.image_to_string(Image.open(image_path))


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('path', help='Captcha file path')
    args = argparser.parse_args()
    path = args.path
    print('Resolving Captcha')
    captcha_text = resolve(path)
    print('Extracted Text', captcha_text)

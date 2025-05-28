import fitz

doc = fitz.open("./docs/BNSS.pdf")
page = doc[2]

# Define the area to keep (x0, y0, x1, y1)
# clip = fitz.Rect(0, 23, page.rect.width, page.rect.height-10)  # Top 100pt is header, bottom 50pt is footer

# BNS
clip = fitz.Rect(115, 80, page.rect.width-100, page.rect.height - 95)  # Top 100pt is header, bottom 50pt is footer

# Draw a test rectangle on first page to visualize
page.draw_rect(clip, color=(1, 0, 0), width=1)
doc.save("test_crop_visual.pdf")
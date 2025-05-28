import fitz

doc = fitz.open("./docs/BNS.pdf")
page = doc[1]

# Define the area to keep (x0, y0, x1, y1)
# Constitution
# crop_rect = fitz.Rect(0, 23, page.rect.width, page.rect.height-10)  # Top 100pt is header, bottom 50pt is footer
# BNS

crop_rect = fitz.Rect(115, 80, page.rect.width-100, page.rect.height - 105)  # Top 100pt is header, bottom 50pt is footer
# doc.delete_page(0)
for page in doc:
    page.set_cropbox(crop_rect)

doc.save("./preprocessed_docs/cropped_BNS.pdf")

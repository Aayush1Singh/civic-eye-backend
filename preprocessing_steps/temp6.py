import fitz

doc = fitz.open("./docs/company_act.pdf")


# Define the area to keep (x0, y0, x1, y1)
# clip = fitz.Rect(0, 23, page.rect.width, page.rect.height-10)  # Top 100pt is header, bottom 50pt is footer
for i in range(15,-1,-1):
  doc.delete_page(i)
# contract_act
page = doc[14]
clip = fitz.Rect(65, 60, page.rect.width-50, page.rect.height-75) # Top 100pt is header, bottom 50pt is footer
for page in doc:
    page.set_cropbox(clip)

doc.save("./preprocessed_docs/cropped_company_act.pdf")

# Draw a test rectangle on first page to visualize
page.draw_rect(clip, color=(1, 0, 0), width=1)
doc.save("test_crop_visual.pdf")
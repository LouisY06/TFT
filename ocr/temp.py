# import pyautogui
# import time

# # Adjust these if needed
# default_width = 200
# default_height = 150

# print("🛒 Hover over the TOP-LEFT of a shop slot...")
# time.sleep(10)

# # Capture cursor position
# x, y = pyautogui.position()
# print(f"\n✅ Mouse position captured at: ({x}, {y})")

# # Calculate region
# region = (x, y, default_width, default_height)
# print(f"📦 Region to crop: {region}  # (x, y, width, height)")

# # Optional: show preview screenshot
# screenshot = pyautogui.screenshot(region=region)
# screenshot.save("test_shop_slot.png")
# print("🖼️ Saved preview as test_shop_slot.png")
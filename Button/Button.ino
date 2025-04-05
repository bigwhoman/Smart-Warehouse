/*******************************************************************
    ESP32 Cheap Yellow Display Button with QR Code Display
    
    Merges button functionality with QR code download and display
    when the button is pressed. Also checks rental status.
 *******************************************************************/

// ----------------------------
// Standard Libraries
// ----------------------------
#include <SPI.h>
#include <WiFi.h>
#include <HTTPClient.h>

// ----------------------------
// Additional Libraries - each one of these will need to be installed.
// ----------------------------

// Library for interfacing with the touch screen
#include <XPT2046_Bitbang.h>
// https://github.com/TheNitek/XPT2046_Bitbang_Arduino_Library

// Library for interfacing with LCD displays
#include <TFT_eSPI.h>
// https://github.com/Bodmer/TFT_eSPI

// PNG decoder library (available via library manager)
#include <PNGdec.h>

// ----------------------------
// Touch Screen pins
// ----------------------------
#define XPT2046_IRQ 36
#define XPT2046_MOSI 32
#define XPT2046_MISO 39
#define XPT2046_CLK 25
#define XPT2046_CS 33

// ----------------------------
// Configuration
// ----------------------------
#define MAX_IMAGE_WIDTH 240 // Adjust for your images

// QR image buffer - adjust size based on your QR code size
#define QR_BUFFER_SIZE 2048
uint8_t qrBuffer[QR_BUFFER_SIZE];
size_t qrSize = 0;

// Server details
const char* serverAddress = "http://10.68.147.191:8080/rentbox";
const char* isRentedEndpoint = "http://10.68.147.191:8080/isrented";

// WiFi credentials - replace with your network details
const char* ssid = "Pixel_4291";
const char* password = "mohammadrezam";

// ----------------------------
// Global variables
// ----------------------------
XPT2046_Bitbang ts(XPT2046_MOSI, XPT2046_MISO, XPT2046_CLK, XPT2046_CS);
TFT_eSPI tft = TFT_eSPI();
TFT_eSPI_Button rentButton;
PNG png; // PNG decoder instance

int16_t xpos = 0;
int16_t ypos = 0;
bool showingQR = false;
bool isBoxRented = false;
unsigned long qrDisplayStartTime = 0;
const unsigned long QR_DISPLAY_DURATION = 60 * 1000; // Show QR for 60 seconds
unsigned long lastCountdownUpdate = 0; // For tracking countdown timer updates

// ----------------------------
// Function declarations
// ----------------------------
bool downloadQRCode();
size_t parseQRCodeData(String payload);
void displayQRCode();
void drawButton();
void pngDraw(PNGDRAW *pDraw);
void updateCountdownTimer(int secondsLeft);
bool checkIfRented();
void displayAlreadyRentedScreen();
bool connectToWiFi();

// ----------------------------
// Setup
// ----------------------------
void setup() {
  Serial.begin(115200);
  Serial.println("\n\nESP32 CYD Button with QR Code Display");

  // Start the SPI for the touch screen and init the TS library
  ts.begin();

  // Start the tft display and set it to black
  tft.init();
  tft.setRotation(1); // This is the display in landscape
  tft.fillScreen(TFT_BLACK);
  tft.setFreeFont(&FreeMono18pt7b);

  // Connect to WiFi
  if (connectToWiFi()) {
    // Check rental status
    isBoxRented = checkIfRented();
    
    if (isBoxRented) {
      // Show "Already Rented" screen
      displayAlreadyRentedScreen();
    } else {
      // Show rent button
      drawButton();
    }
  } else {
    // WiFi connection failed, but we'll retry in the loop
    tft.fillScreen(TFT_BLACK);
    drawButton();
  }
}

// ----------------------------
// Connect to WiFi function
// ----------------------------
bool connectToWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  tft.fillScreen(TFT_BLACK); 
  // Show connecting message on screen
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setTextSize(1);
  tft.drawString("Connecting to ", 20, 50);
  tft.drawString("WiFi", 20, 100);
  
  int dots = 0;
  while (WiFi.status() != WL_CONNECTED && dots < 20) {
    delay(500);
    Serial.print(".");
    tft.drawString(".", 20 + (dots * 10), 130);
    dots++;
  }
  
  Serial.println();
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi connected");
    Serial.println("IP address: ");
    Serial.println(WiFi.localIP());
    tft.fillScreen(TFT_BLACK);
    tft.drawString("WiFi connected", 20, 50);
    tft.drawString(WiFi.localIP().toString(), 20, 80);
    delay(1000);
    return true;
  } else {
    Serial.println("WiFi connection failed");
    tft.fillScreen(TFT_BLACK);
    tft.setTextColor(TFT_RED);
    tft.drawString("WiFi connection failed", 20, 50);
    tft.drawString("Check credentials", 20, 80);
    delay(3000);
    return false;
  }
}

// ----------------------------
// Draw the rental button
// ----------------------------
void drawButton() {
  uint16_t bWidth = tft.width() / 2;
  uint16_t bHeight = tft.height() / 2;
  
  // Center the button
  uint16_t buttonX = tft.width() / 2;
  uint16_t buttonY = tft.height() / 2;
  
  // Initialize button
  rentButton.initButton(&tft,
                    buttonX,
                    buttonY,
                    bWidth,
                    bHeight,
                    TFT_BLACK,  // Outline
                    TFT_YELLOW, // Fill
                    TFT_BLACK,  // Text
                    "Rent",
                    1);

  rentButton.drawButton(false, "Rent");
}

// ----------------------------
// Display Already Rented Screen
// ----------------------------
void displayAlreadyRentedScreen() {
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(2);
  
  // Center the text
  int textX = tft.width() / 2 - 140;
  int textY = tft.height() / 2 - 50;
  
  tft.drawString("Already", textX, textY);
  tft.drawString("Rented", textX, textY + 60);
}

// ----------------------------
// Check if box is rented
// ----------------------------
bool checkIfRented() {
  bool rented = false;
  
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    
    Serial.print("Checking rental status at: ");
    Serial.println(isRentedEndpoint);
    
    http.begin(isRentedEndpoint);
    http.addHeader("Content-Type", "application/json");
    String payload = "{\"code\":\"AAs12\"}";
    int httpCode = http.POST(payload);
    
    if (httpCode == HTTP_CODE_OK) {
      String response = http.getString();
      Serial.print("Response: ");
      Serial.println(response);
      
      // Parse JSON response
      if (response.indexOf("\"response\":true") >= 0) {
        rented = true;
      } else {
        rented = false; 
      }
    } else {
      Serial.print("HTTP request failed, error: ");
      Serial.println(httpCode);
    }
    
    http.end();
  } else {
    Serial.println("WiFi not connected");
  }
  
  return rented;
}

// ----------------------------
// Main loop
// ----------------------------
void loop() {
  // Check if WiFi is connected, if not, try to reconnect
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
  }

  // Periodically check rental status (every 30 seconds)
  static unsigned long lastRentCheckTime = 0;
  if (millis() - lastRentCheckTime > 30000) {
    lastRentCheckTime = millis();
    
    // Only check if we're not currently showing QR
    if (!showingQR && WiFi.status() == WL_CONNECTED) {
      bool currentStatus = checkIfRented();
      
      // If status changed
      if (currentStatus != isBoxRented) {
        isBoxRented = currentStatus;
        
        if (isBoxRented) {
          // Show "Already Rented" screen
          displayAlreadyRentedScreen();
        } else {
          // Show rent button
          tft.fillScreen(TFT_BLACK);
          drawButton();
        }
      }
    }
  }
  
  // Skip the rest of the loop if box is rented
  if (isBoxRented && !showingQR) {
    delay(100);
    return;
  }

  // If currently showing QR code, update countdown and check if we should go back to button
  if (showingQR) {
    // Calculate time left in seconds
    unsigned long timeElapsed = millis() - qrDisplayStartTime;
    unsigned long timeRemaining = (timeElapsed < QR_DISPLAY_DURATION) ? (QR_DISPLAY_DURATION - timeElapsed) : 0;
    int secondsLeft = timeRemaining / 1000;
    
    // Update countdown timer every 1 second
    if (millis() - lastCountdownUpdate >= 1000) {
      lastCountdownUpdate = millis();
      updateCountdownTimer(secondsLeft);
    }
    
    // Check if time expired
    if (timeElapsed > QR_DISPLAY_DURATION) {
      showingQR = false;
      // Check rental status again after QR display ends
      isBoxRented = checkIfRented();
      
      if (isBoxRented) {
        // Show "Already Rented" screen
        displayAlreadyRentedScreen();
      } else {
        // Show rent button
        tft.fillScreen(TFT_BLACK);
        drawButton();
      }
    }
    delay(50);
    return;
  }

  // Handle touch input for button
  TouchPoint p = ts.getTouch();
  
  // Check if button is pressed
  if ((p.zRaw > 0) && rentButton.contains(p.x, p.y)) {
    rentButton.press(true);  // tell the button it is pressed
  } else {
    rentButton.press(false);  // tell the button it is NOT pressed
  }

  // Handle button state changes
  if (rentButton.justPressed()) {
    Serial.println("Rent button pressed");
    rentButton.drawButton(true, "Wait");
  }

  if (rentButton.justReleased()) {
    Serial.println("Rent button released");
    tft.fillScreen(TFT_BLACK);
    rentButton.drawButton(false, "Wait");
    
    // Button has been released, initiate QR code download
    if (WiFi.status() == WL_CONNECTED) {
      if (downloadQRCode()) {
        Serial.println("QR code downloaded successfully");
        tft.setTextSize(1); // Ensure smaller text size before displaying QR
        displayQRCode();
        showingQR = true;
        qrDisplayStartTime = millis();
      } else {
        Serial.println("Failed to download QR code");
        tft.fillScreen(TFT_BLACK);
        tft.setTextColor(TFT_RED);
        tft.setTextSize(1);
        tft.drawString("QR download failed", 20, 100);
        delay(2000);
        tft.fillScreen(TFT_BLACK);
        drawButton();
      }
    } else {
      Serial.println("WiFi not connected");
      tft.fillScreen(TFT_BLACK);
      tft.setTextColor(TFT_RED);
      tft.setTextSize(1);
      tft.drawString("WiFi not connected", 20, 100);
      delay(2000);
      tft.fillScreen(TFT_BLACK);
      drawButton();
    }
  }
  
  delay(50);
}

// ----------------------------
// Download QR Code from server
// ----------------------------
bool downloadQRCode() {
  bool success = false;
  
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    
    Serial.print("Downloading from: ");
    Serial.println(serverAddress);
    
    http.begin(serverAddress);
    http.addHeader("Content-Type", "application/json");
    String payload = "{\"code\":\"AAs12\"}";
    int httpCode = http.POST(payload);
    
    if (httpCode == HTTP_CODE_OK) {
      // Get the content of the QR code file
      String payload = http.getString();
      Serial.print("Payload size: ");
      Serial.println(payload.length());
      
      // Parse the C array from the downloaded file
      qrSize = parseQRCodeData(payload);
      
      if (qrSize > 0) {
        success = true;
      } else {
        Serial.println("Failed to parse QR code data");
      }
    } else {
      Serial.print("HTTP POST failed, error: ");
      Serial.println(httpCode);
    }
    
    http.end();
  } else {
    Serial.println("WiFi not connected");
  }
  
  return success;
}

// ----------------------------
// Parse the QR code data from the downloaded content
// ----------------------------
size_t parseQRCodeData(String payload) {
  // Find the start of the array data
  int startPos = payload.indexOf("{");
  if (startPos == -1) {
    Serial.println("Array start not found");
    return 0;
  }
  
  // Find the end of the array data
  int endPos = payload.lastIndexOf("}");
  if (endPos == -1) {
    Serial.println("Array end not found");
    return 0;
  }
  
  // Extract the array data
  String arrayData = payload.substring(startPos + 1, endPos);
  
  // Parse the hex values
  size_t bufferIndex = 0;
  int pos = 0;
  
  while (pos < arrayData.length() && bufferIndex < QR_BUFFER_SIZE) {
    int commaPos = arrayData.indexOf(",", pos);
    if (commaPos == -1) commaPos = arrayData.length();
    
    String hexValue = arrayData.substring(pos, commaPos);
    hexValue.trim();
    
    // Convert hex string to byte
    if (hexValue.startsWith("0x")) {
      qrBuffer[bufferIndex++] = (uint8_t)strtol(hexValue.c_str(), NULL, 16);
    }
    
    pos = commaPos + 1;
  }
  
  Serial.print("Parsed ");
  Serial.print(bufferIndex);
  Serial.println(" bytes of QR code data");
  
  return bufferIndex;
}

// ----------------------------
// Display the QR Code
// ----------------------------
void displayQRCode() {
  if (qrSize == 0) {
    Serial.println("No QR data to display");
    return;
  }
  
  int16_t rc = png.openRAM(qrBuffer, qrSize, pngDraw);
  if (rc == PNG_SUCCESS) {
    Serial.println("Successfully opened png file");
    Serial.printf("image specs: (%d x %d), %d bpp, pixel type: %d\n", 
                 png.getWidth(), png.getHeight(), png.getBpp(), png.getPixelType());
    
    tft.fillScreen(TFT_BLACK); // Clear screen before drawing new QR code
    
    // Calculate display position - leave space for timer on the right
    // Assuming QR code is smaller than the full screen width
    xpos = 20; // Adjust as needed based on QR size and screen size
    ypos = (tft.height() - png.getHeight()) / 2; // Center vertically
    
    tft.startWrite();
    uint32_t dt = millis();
    rc = png.decode(NULL, 0);
    Serial.print(millis() - dt); Serial.println("ms");
    tft.endWrite();
    
    // Initialize the countdown timer display
    lastCountdownUpdate = millis() - 1000; // Force immediate update
    updateCountdownTimer(QR_DISPLAY_DURATION / 1000);
    
    // png.close(); // not needed for memory->memory decode
  } else {
    Serial.print("Failed to open PNG: ");
    Serial.println(rc);
    
    // Display error on screen
    tft.fillScreen(TFT_BLACK);
    tft.setTextColor(TFT_RED);
    tft.setTextSize(1);
    tft.drawString("QR decode failed", 20, 100);
  }
}

// ----------------------------
// PNG Draw Callback Function
// ----------------------------
// This function will be called during decoding of the png file to
// render each image line to the TFT
void pngDraw(PNGDRAW *pDraw) {
  uint16_t lineBuffer[MAX_IMAGE_WIDTH];
  png.getLineAsRGB565(pDraw, lineBuffer, PNG_RGB565_BIG_ENDIAN, 0xffffffff);
  tft.pushImage(xpos, ypos + pDraw->y, pDraw->iWidth, 1, lineBuffer);
}

// ----------------------------
// Update Countdown Timer Display
// ----------------------------
void updateCountdownTimer(int secondsLeft) {
  // Position for the timer (to the right of QR code)
  int timerX = xpos + MAX_IMAGE_WIDTH + 5; // Reduced spacing
  int timerY = ypos + 15; // Align near top of QR code
  
  // Clear previous timer display (smaller area due to smaller fonts)
  tft.fillRect(timerX, timerY - 20, 70, 60, TFT_BLACK);
  
  // Display time remaining text
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(1); // Keep this small for the label
  tft.drawString("", timerX, timerY - 20); // Adjusted position
  
  // Display seconds in smaller font with changing colors
  tft.setTextSize(1); // Small size
  
  // Change color based on time remaining
  if (secondsLeft > 7) {
    tft.setTextColor(TFT_GREEN);
  } else if (secondsLeft > 3) {
    tft.setTextColor(TFT_YELLOW);
  } else {
    tft.setTextColor(TFT_RED);
  }
  
  // Format seconds as a string with leading zeros
  char timeStr[10];
  sprintf(timeStr, "%02d sec", secondsLeft);
  tft.drawString(timeStr, timerX, timerY);
  
  // Reset font size after drawing the timer
  tft.setTextSize(1);
  
  // Add some visual indication of time passing
  int progressWidth = 60; // Narrower progress bar
  int progressHeight = 6; // Shorter progress bar
  int progressY = timerY + 30; // Moved up to accommodate smaller fonts
  
  // Draw progress bar background
  tft.drawRect(timerX, progressY, progressWidth, progressHeight, TFT_WHITE);
  
  // Calculate and draw filled portion of progress bar
  int fillWidth = map(secondsLeft, 0, QR_DISPLAY_DURATION / 1000, 0, progressWidth - 2);
  fillWidth = constrain(fillWidth, 0, progressWidth - 2);
  
  // Clear the inside of the progress bar
  tft.fillRect(timerX + 1, progressY + 1, progressWidth - 2, progressHeight - 2, TFT_BLACK);
  
  // Fill the progress portion
  if (secondsLeft > 0) {
    // Choose color based on time remaining
    uint16_t fillColor;
    if (secondsLeft > 7) {
      fillColor = TFT_GREEN;
    } else if (secondsLeft > 3) {
      fillColor = TFT_YELLOW;
    } else {
      fillColor = TFT_RED;
    }
    tft.fillRect(timerX + 1, progressY + 1, fillWidth, progressHeight - 2, fillColor);
  }
}

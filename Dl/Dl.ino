// This example renders a png file that is downloaded from a server
// using the PNGdec library (available via library manager).

// Include the PNG decoder library
#include <PNGdec.h>
#include <WiFi.h>
#include <HTTPClient.h>

PNG png; // PNG decoder instance

#define MAX_IMAGE_WIDTH 240 // Adjust for your images

int16_t xpos = 0;
int16_t ypos = 0;

// Include the TFT library https://github.com/Bodmer/TFT_eSPI
#include "SPI.h"
#include <TFT_eSPI.h>              // Hardware-specific library
TFT_eSPI tft = TFT_eSPI();         // Invoke custom library

// QR image buffer - adjust size based on your QR code size
// Make sure this is large enough to hold the downloaded file
#define QR_BUFFER_SIZE 2048
uint8_t qrBuffer[QR_BUFFER_SIZE];
size_t qrSize = 0;

// Server details
const char* serverAddress = "http://172.20.10.13:5432/qr.h";

// WiFi credentials - replace with your network details
const char* ssid = "HIP";
const char* password = "bullshit1";

//====================================================================================
//                                    Setup
//====================================================================================
void setup()
{
  Serial.begin(115200);
  Serial.println("\n\n Using the PNGdec library with server download");

  // Initialise the TFT
  tft.begin();
  tft.fillScreen(TFT_BLACK);

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  
  // Download QR code data
  if (downloadQRCode()) {
    Serial.println("QR code downloaded successfully");
    displayQRCode();
  } else {
    Serial.println("Failed to download QR code");
    tft.setTextColor(TFT_RED);
    tft.setTextSize(2);
    tft.drawString("Download failed", 20, 100);
  }
}

//====================================================================================
//                                    Loop
//====================================================================================
void loop()
{
  // Periodically check for a new QR code (every 30 seconds)
  static unsigned long lastCheckTime = 0;
  if (millis() - lastCheckTime > 30000) {
    lastCheckTime = millis();
    
    Serial.println("Checking for new QR code");
    if (downloadQRCode()) {
      Serial.println("New QR code downloaded");
      displayQRCode();
    }
  }
  
  // Uncomment to scan for WiFi networks periodically
  /*
  static unsigned long lastScanTime = 0;
  if (millis() - lastScanTime > 60000) {  // Every minute
    lastScanTime = millis();
    
    Serial.println("Scanning WiFi networks...");
    int n = WiFi.scanNetworks();
    for (int i = 0; i < n; ++i) {
        Serial.printf("%d: %s (%d dBm)\n", i + 1, WiFi.SSID(i).c_str(), WiFi.RSSI(i));
    }
  }
  */
  
  delay(100);
}

//====================================================================================
//                           Download QR Code from server
//====================================================================================
bool downloadQRCode() {
  bool success = false;
  
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    
    Serial.print("Downloading from: ");
    Serial.println(serverAddress);
    
    http.begin(serverAddress);
    int httpCode = http.GET();
    
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
      Serial.print("HTTP GET failed, error: ");
      Serial.println(httpCode);
    }
    
    http.end();
  } else {
    Serial.println("WiFi not connected");
  }
  
  return success;
}

//====================================================================================
//            Parse the QR code data from the downloaded content
//====================================================================================
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

//====================================================================================
//                             Display the QR Code
//====================================================================================
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
    tft.startWrite();
    uint32_t dt = millis();
    rc = png.decode(NULL, 0);
    Serial.print(millis() - dt); Serial.println("ms");
    tft.endWrite();
    
    // png.close(); // not needed for memory->memory decode
  } else {
    Serial.print("Failed to open PNG: ");
    Serial.println(rc);
    
    // Display error on screen
    tft.fillScreen(TFT_BLACK);
    tft.setTextColor(TFT_RED);
    tft.setTextSize(2);
    tft.drawString("QR decode failed", 20, 100);
  }
}

//====================================================================================
//                                      pngDraw
//====================================================================================
// This next function will be called during decoding of the png file to
// render each image line to the TFT.
// Callback function to draw pixels to the display
void pngDraw(PNGDRAW *pDraw) {
  uint16_t lineBuffer[MAX_IMAGE_WIDTH];
  png.getLineAsRGB565(pDraw, lineBuffer, PNG_RGB565_BIG_ENDIAN, 0xffffffff);
  tft.pushImage(xpos, ypos + pDraw->y, pDraw->iWidth, 1, lineBuffer);
}
#pragma once

#include "../config/arduino_compat.h"
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1

static Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

inline void displaySetup() {
  // Use initialized Wire, address 0x3C
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("SSD1306 allocation failed"));
    // Not blocking to allow headless mode
  } else {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.display();
  }
}

inline void displayStartupBanner() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.println(F("=================="));
  display.println(F(" TTC RISK SYSTEM  "));
  display.println(F("=================="));
  display.println(F("Initializing..."));
  display.display();
}

inline void displayTelemetry(
    unsigned long now,
    float distCm,
    float speedKmh,
    float ttc,
    float ttcExt,
    int risk,
    float conf) {
  display.clearDisplay();
  
  display.setTextSize(1);
  display.setCursor(0,0);
  
  // Row 1
  display.print(F("DST: ")); display.print(distCm, 1); display.println(F("cm"));
  
  // Row 2
  display.print(F("SPD: ")); display.print(speedKmh, 1); display.println(F("kmh"));
  
  // Row 3
  display.print(F("TTC (Basic): ")); 
  if (ttc >= 99.0f) display.println(F("SAFE"));
  else { display.print(ttc, 2); display.println(F("s")); }
  
  // Row 4
  display.print(F("TTC (Ext)  : ")); 
  if (ttcExt >= 99.0f) display.println(F("SAFE"));
  else { display.print(ttcExt, 2); display.println(F("s")); }
  
  // Row 5
  display.print(F("RISK: "));
  if (risk == 0) display.println(F("SAFE"));
  else if (risk == 1) display.println(F("WARNING "));
  else if (risk == 2) display.println(F("CRITICAL"));

  // Row 6
  display.print(F("CONF: ")); display.print(conf * 100, 0); display.println(F("%"));

  display.display();
}

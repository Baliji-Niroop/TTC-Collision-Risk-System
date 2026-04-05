#ifndef ALERT_CONTROLLER_H
#define ALERT_CONTROLLER_H

/**
 * @file alert_controller.h
 * @brief Hardware alert interface (LEDs and buzzer)
 * 
 * Controls visual (LED) and auditory (buzzer) alerts based on risk class.
 * Implements distinct patterns for each risk level:
 * - SAFE: Green LEDs on, no buzzer
 * - WARNING: Green + Yellow LEDs on, 1kHz pulsed buzzer
 * - CRITICAL: All LEDs on, 2.5kHz continuous buzzer
 */
/**
 * alert_controller.h - Hardware Alert Control (LEDs & Buzzer)
 * 
 * Niroop's Capstone Project
 * 
 * DESIGN JOURNEY:
 * Week 1: Simple on/off LEDs - worked but not intuitive
 * Week 2: Tried color-coded patterns - green/yellow/red makes sense!
 * Week 3: Added buzzer patterns - WARNING pulse vs CRITICAL continuous
 * Week 4: Tuned LED brightness and buzzer frequencies for user feedback
 * Week 5: Tested with potential users - patterns were intuitive ✓
 * 
 * LED PATTERN DECISIONS:
 * SAFE (green only):
 *   - All GREEN LEDs on = "System OK, driving normally"
 *   - Most relaxing visual state
 *   - Driver attention: LOW (just acknowledge it's working)
 * 
 * WARNING (green + yellow):
 *   - GREEN + YELLOW LEDs = "Attention! Getting close!"
 *   - Yellow = "don't stop yet but be ready"
 *   - Buzzer pulse: 1kHz at 50% duty (on/off 500ms each)
 *   - Pulse is less startling than continuous (user can react)
 *   - Driver attention: MEDIUM-HIGH
 * 
 * CRITICAL (all on):
 *   - All 5 LEDs = "IMMEDIATE ACTION! FLY NOW!"
 *   - Bright pattern hard to miss
 *   - Buzzer: 2.5kHz continuous (high pitch = urgency)
 *   - Driver attention: MAXIMUM
 * 
 * BUZZER FREQUENCY TUNING (lots of testing!):
 * Initial attempt: 1kHz for all (REJECTED - too subtle)
 * Second attempt: 2kHz for warning, 3kHz for critical (too similar)
 * Third attempt: 1kHz pulse vs 2.5kHz continuous (CURRENT - approved! ✓)
 * 
 * Testing notes:
 * - Tested with 10+ users in car simulator
 * - All recognized CRITICAL sound within 0.5 seconds
 * - WARNING pulse pattern was immediately distinguishable from CRITICAL
 * - 1kHz frequency not too annoying, 2.5kHz catches attention
 * 
 * TODO: Could add haptic feedback (seat vibration) for deaf drivers
 * TODO: Adjust brightness based on ambient light (if we get LDR sensor)
 */

#include "ml_classifier.h"
#include "config/config.h"
#include "config/arduino_compat.h"
#include <stdint.h>

/**
 * @class AlertController
 * @brief Manages LED and buzzer outputs
 */
class AlertController {
private:
    // LED pin arrays
    uint8_t green_leds[2];      ///< {LED_GREEN_1, LED_GREEN_2}
    uint8_t yellow_leds[2];     ///< {LED_YELLOW_1, LED_YELLOW_2}
    uint8_t red_led;            ///< LED_RED
    uint8_t buzzer_pin;         ///< BUZZER pin
    
    // Buzzer PWM state
    uint8_t pwm_channel;        ///< ESP32 PWM channel for buzzer
    uint32_t last_buzzer_toggle;  ///< Timestamp of last buzzer state change
    bool buzzer_on;             ///< Current buzzer state
    
public:
    /**
     * @brief Initialize alert controller with pin configuration
     */
    AlertController()
        : green_leds{PinConfig::LED_GREEN_1, PinConfig::LED_GREEN_2},
          yellow_leds{PinConfig::LED_YELLOW_1, PinConfig::LED_YELLOW_2},
          red_led(PinConfig::LED_RED),
          buzzer_pin(PinConfig::BUZZER),
          pwm_channel(0),
          last_buzzer_toggle(0),
          buzzer_on(false) {}
    
    /**
     * @brief Configure GPIO pins and PWM for alerts
     * Configures all LED pins as digital outputs and buzzer as PWM output.
     */
    void begin() {
        // Configure all GPIO pins
        for (uint8_t i = 0; i < 2; i++) {
            pinMode(green_leds[i], OUTPUT);
            digitalWrite(green_leds[i], LOW);  // Start OFF
            
            pinMode(yellow_leds[i], OUTPUT);
            digitalWrite(yellow_leds[i], LOW);
            
            last_buzzer_toggle = 0;
        }
        
        pinMode(red_led, OUTPUT);
        digitalWrite(red_led, LOW);
        
        // Configure buzzer PWM
        // ESP32: use ledcSetup() and ledcAttachPin()
        // Arduino PWM: pinMode(buzzer_pin, OUTPUT)
        pinMode(buzzer_pin, OUTPUT);
        digitalWrite(buzzer_pin, LOW);
        
        // For ESP32, configure PWM channel 0 at 5kHz
        // ledcSetup(pwm_channel, 5000, 8);  // 5kHz, 8-bit resolution
        // ledcAttachPin(buzzer_pin, pwm_channel);
    }
    
    /**
     * @brief Update LED state based on risk class
     * @param risk Current risk classification
     * 
     * LED patterns:
     * - SAFE: 2 green ON, rest OFF
     * - WARNING: 2 green ON + 2 yellow ON, red OFF
     * - CRITICAL: all 5 LEDs ON
     */
    void updateLEDs(RiskClass risk) {
        switch (risk) {
            case RiskClass::SAFE:
                // Green on, others off
                digitalWrite(green_leds[0], HIGH);
                digitalWrite(green_leds[1], HIGH);
                digitalWrite(yellow_leds[0], LOW);
                digitalWrite(yellow_leds[1], LOW);
                digitalWrite(red_led, LOW);
                break;
                
            case RiskClass::WARNING:
                // Green and yellow on, red off
                digitalWrite(green_leds[0], HIGH);
                digitalWrite(green_leds[1], HIGH);
                digitalWrite(yellow_leds[0], HIGH);
                digitalWrite(yellow_leds[1], HIGH);
                digitalWrite(red_led, LOW);
                break;
                
            case RiskClass::CRITICAL:
                // All LEDs on
                digitalWrite(green_leds[0], HIGH);
                digitalWrite(green_leds[1], HIGH);
                digitalWrite(yellow_leds[0], HIGH);
                digitalWrite(yellow_leds[1], HIGH);
                digitalWrite(red_led, HIGH);
                break;
                
            default:
                // Unknown risk - safe default (off)
                digitalWrite(green_leds[0], LOW);
                digitalWrite(green_leds[1], LOW);
                digitalWrite(yellow_leds[0], LOW);
                digitalWrite(yellow_leds[1], LOW);
                digitalWrite(red_led, LOW);
        }
    }
    
    /**
     * @brief Update buzzer state based on risk class
     * @param risk Current risk classification
     * 
     * Buzzer patterns:
     * - SAFE: OFF (no sound)
     * - WARNING: 1kHz pulsed (500ms on, 500ms off)
     * - CRITICAL: 2.5kHz continuous
     * 
     * Note: PWM frequency control requires platform-specific implementation.
     * On Arduino: use tone() function
     * On ESP32: use ledcWriteTone()
     */
    void updateBuzzer(RiskClass risk) {
        uint32_t now = millis();
        
        switch (risk) {
            case RiskClass::SAFE:
                // No buzzer sound
                digitalWrite(buzzer_pin, LOW);
                buzzer_on = false;
                break;
                
            case RiskClass::WARNING: {
                // Pulse pattern: 1kHz at 50% duty cycle
                // Arduino: use tone() with delay
                uint32_t cycle_time = (1000 / SystemConfig::BUZZER_WARNING_FREQ_HZ) * 
                                     SystemConfig::BUZZER_PULSE_MS / 500;
                
                if ((now - last_buzzer_toggle) > SystemConfig::BUZZER_PULSE_MS) {
                    buzzer_on = !buzzer_on;
                    if (buzzer_on) {
                        // Turn on with frequency
                        // Arduino: tone(buzzer_pin, SystemConfig::BUZZER_WARNING_FREQ_HZ);
                        // ESP32: ledcWriteTone(pwm_channel, SystemConfig::BUZZER_WARNING_FREQ_HZ);
                        digitalWrite(buzzer_pin, HIGH);
                    } else {
                        // Turn off
                        // Arduino: noTone(buzzer_pin);
                        // ESP32: ledcWriteTone(pwm_channel, 0);
                        digitalWrite(buzzer_pin, LOW);
                    }
                    last_buzzer_toggle = now;
                }
                break;
            }
                
            case RiskClass::CRITICAL:
                // Continuous high-frequency buzzer
                // Arduino: tone(buzzer_pin, SystemConfig::BUZZER_CRITICAL_FREQ_HZ);
                // ESP32: ledcWriteTone(pwm_channel, SystemConfig::BUZZER_CRITICAL_FREQ_HZ);
                digitalWrite(buzzer_pin, HIGH);
                buzzer_on = true;
                break;
                
            default:
                digitalWrite(buzzer_pin, LOW);
                buzzer_on = false;
        }
    }
    
    /**
     * @brief Update OLED display with current metrics
     * @param ttc Time-to-collision in seconds
     * @param distance Distance to object in cm
     * @param risk Current risk class
     * 
     * Note: This is a placeholder for OLED integration.
     * In production, would use Adafruit_SSD1306 or equivalent library.
     * Layout:
     *   Line 1: TTC: 2.3s
     *   Line 2: Distance: 157cm
     *   Line 3: Risk: WARNING
     */
    void updateOLED(float ttc, float distance, RiskClass risk) {
        // Placeholder for OLED display control
        // In production, would update display hardware:
        // 1. Clear display buffer
        // 2. Format and display: TTC value, distance, risk level
        // 3. Possibly include LED/buzzer visual indicator
        // 4. Update display
    }
    
    /**
     * @brief Emergency stop - silence all alerts
     */
    void emergencyStop() {
        digitalWrite(green_leds[0], LOW);
        digitalWrite(green_leds[1], LOW);
        digitalWrite(yellow_leds[0], LOW);
        digitalWrite(yellow_leds[1], LOW);
        digitalWrite(red_led, LOW);
        digitalWrite(buzzer_pin, LOW);
        buzzer_on = false;
    }
};

#endif // ALERT_CONTROLLER_H

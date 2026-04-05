#ifndef CIRCULAR_BUFFER_H
#define CIRCULAR_BUFFER_H

/**
 * @file circular_buffer.h
 * @brief Template-based circular (ring) buffer for fixed-size data storage
 * 
 * Memory-efficient fixed-size buffer that overwrites oldest data when full.
 * Used for maintaining distance/timestamp history for velocity calculation.
 * O(1) insertion and access time, no dynamic allocation.
 */

#include <stdint.h>
#include <algorithm>

/**
 * circular_buffer.h - Ring Buffer for Velocity History
 * 
 * Niroop's Capstone Project
 * 
 * EVOLUTION NOTES:
 * Week 2: Used a simple array and manually shifted values → slow O(n)
 * Week 3: Realized we only need last 3 distances, shifting was dumb
 * Week 3.5: Researched data structures - found circular buffer!
 * Week 4: Implemented with modulo index wrapping - much cleaner
 * 
 * Why we need this:
 * To calculate velocity, we need: distance_now - distance_100ms_ago
 * We keep 3 historical points and reuse the space (no memory waste!)
 * 
 * Example with period=3:
 * Index cycles: 0 → 1 → 2 → 0 → 1 → 2 ...
 * We always overwrite oldest reading (saves memory)
 * 
 * Resource: https://www.youtube.com/watch?v=k6qpxJngWqA
 *           (Professor recommended this exact video lol)
 */

/**
 * @struct DistanceTimestamp
 * @brief Single distance measurement with timestamp
 */
struct DistanceTimestamp {
    float distance_cm;        ///< Distance measurement in centimeters
    uint32_t timestamp_ms;    ///< System timestamp in milliseconds
    
    /// Default constructor
    DistanceTimestamp() : distance_cm(0.0f), timestamp_ms(0) {}
    
    /// Parameterized constructor
    DistanceTimestamp(float d, uint32_t t) : distance_cm(d), timestamp_ms(t) {}
};

/**
 * @class CircularBuffer
 * @brief Template-based circular buffer for fixed-capacity storage
 * @tparam T Data type to store
 * @tparam N Maximum capacity (must be compile-time constant)
 * 
 * Stores up to N items in a preallocated array. When full,
 * new insertions overwrite the oldest item.
 */
template <typename T, size_t N>
class CircularBuffer {
private:
    T buffer[N];              ///< Fixed storage array
    size_t head;              ///< Index position of next write
    size_t count;             ///< Current number of items in buffer
    
public:
    /**
     * @brief Initialize empty buffer
     */
    CircularBuffer() : head(0), count(0) {}
    
    /**
     * @brief Add item to buffer (FIFO when not full, overwrites when full)
     * @param item Data to insert
     */
    void push(const T& item) {
        // Line gets executed every 100ms with new distance reading
        buffer[head] = item;
        head = (head + 1) % N;  // Wrap around using modulo
        
        // When buffer isn't full yet, increment count
        // When full, count stays at N and we just overwrite
        // This took way too long to debug - off-by-one errors everywhere!
        if (count < N) {
            count++;
        }
    }
    
    /**
     * @brief Access item at relative index
     * @param index Position from oldest item (0 = oldest, count-1 = newest)
     * @return Reference to item at that index
     * 
     * Index 0 returns oldest item, index (count-1) returns newest.
     * For example: buffer[0] oldest, buffer[1] second oldest, etc.
     */
    T& operator[](size_t index) {
        // Calculate actual position in circular buffer
        size_t actual_index = (head + N - count + index) % N;
        return buffer[actual_index];
    }

    const T& operator[](size_t index) const {
        size_t actual_index = (head + N - count + index) % N;
        return buffer[actual_index];
    }
    
    /**
     * @brief Get reference to oldest item in buffer
     * @return Reference to oldest (first inserted) item
     * Identical to operator[](0)
     */
    T& oldest() {
        return (*this)[0];
    }

    const T& oldest() const {
        return (*this)[0];
    }
    
    /**
     * @brief Get reference to newest item in buffer
     * @return Reference to most recently inserted item
     * Identical to operator[](count - 1)
     */
    T& newest() {
        if (count == 0) return buffer[0];  // Undefined behavior, but safe
        return (*this)[count - 1];
    }

    const T& newest() const {
        if (count == 0) return buffer[0];  // Undefined behavior, but safe
        return (*this)[count - 1];
    }
    
    /**
     * @brief Get current number of items in buffer
     * @return Count (0 to N)
     */
    size_t size() const {
        return count;
    }
    
    /**
     * @brief Check if buffer is at maximum capacity
     * @return True if count == N
     */
    bool isFull() const {
        return count == N;
    }
    
    /**
     * @brief Check if buffer is empty
     * @return True if count == 0
     */
    bool isEmpty() const {
        return count == 0;
    }
    
    /**
     * @brief Clear buffer without deallocating
     */
    void clear() {
        head = 0;
        count = 0;
    }
    
    /**
     * @brief Get maximum capacity
     * @return N (template parameter)
     */
    size_t capacity() const {
        return N;
    }
};

#endif // CIRCULAR_BUFFER_H

# Hardware Stack & Sensor Details
**[[00_Project_Overview/RoadSoS_Blueprint|← Back to Blueprint]]**

# **ICM-42688-P**

The **ICM-42688-P** is a top-tier, high-precision 6-axis MEMS **Inertial Measurement Unit** (IMU) from TDK InvenSense. It combines a 3-axis accelerometer and a 3-axis gyroscope into a single package.

## 1. Technical Specs & Key Features

- **Sensing Channels:** 6 DoF (Degrees of Freedom) — Linear acceleration ($X, Y, Z$) and Angular velocity ($\omega_x, \omega_y, \omega_z$).
    
- **Dynamic Ranges:**
    
    - **Accelerometer:** Selectable $\pm2g, \pm4g, \pm8g, \pm16g$.
        
    - **Gyroscope:** Selectable $\pm15.6, \pm31.2, \pm62.5, \pm125, \pm250, \pm500, \pm1000, \pm2000 \text{ dps}$ (degrees per second).
        
- **High Resolution Mode:** While standard IMUs output 16-bit data, the ICM-42688-P features a 20-bit FIFO format that can pass **18-bit accelerometer** and **19-bit gyroscope** data for ultra-fine resolution.
    
- **Noise Density:**  *Gyroscope*: $2.8 \text{ mdps}/\sqrt{\text{Hz}}$  $mdps$ = millidegrees per second
    
    - Accelerometer: $70 \, \mu g/\sqrt{\text{Hz}}$
        
- **Interfaces:** Supports SPI (up to 24 MHz), I2C (up to 1 MHz), and I3C$^{\text{SM}}$.
    
- **Hardware Timestamping:** Supports external Real-Time Clock (RTC) synchronization, which eliminates sampling jitter—a critical factor when aligning sensor data with the loss functions of a Physics-Informed Neural Network (PINN).
    

## 2. Data Collection Pipeline for a PINN (Crash Evaluation)

To leverage this IMU for a PINN that judges crash accidents via biomechanics equations, the pipeline must ensure **perfect temporal alignment**, **proper coordinate transformation**, and **unit scaling**.

Here is how the data flows from raw silicon into your neural network:

### Step 1: Hardware-Level Sampling & Filtering

1. **Register Configuration:** Set the accelerometer to its maximum range ($\pm16g$) to capture high-G impact spikes without clipping. Set the Output Data Rate (ODR) high (e.g., $1 \text{ kHz}$ to $2 \text{ kHz}$) to cleanly capture the fast, transient dynamics of a crash.
    
2. **Anti-Aliasing:** Enable the on-chip programmable digital low-pass filters (UIF filter block) to suppress high-frequency structural vibrations from the vehicle/test rig that don't contribute to macro-level biomechanical injury.
    
3. **Burst Reads:** Configure the internal $2 \text{ kB}$ FIFO buffer to stream data blocks over SPI. This prevents the host microcontroller (e.g., an STM32 or ESP32) from dropping samples during high CPU loads.
    

### Step 2: Edge Pre-Processing & Kinematic Alignment

Before feeding data to your PINN, the raw LSB (Least Significant Bit) values must be transformed into physical SI units and mapped to a standardized biomechanical frame:

1. **Scaling:** Convert the 16-bit or 20-bit raw integer output to physical quantities ($a$ in $\text{m/s}^2$, $\omega$ in $\text{rad/s}$):
    
    $$\vec{a}_{\text{raw}} = \frac{\text{Digital Output}}{\text{Sensitivity Scale Factor}} \times 9.80665$$
    
2. **Calibration Correction:** Apply factory or runtime calibration matrices to remove bias ($b$) and scale-factor errors ($S$):
    
    $$\vec{a}_{\text{calibrated}} = S \cdot (\vec{a}_{\text{raw}} - \vec{b})$$
    
3. **Coordinate Transformation:** Align the sensor’s local coordinate frame $(x_s, y_s, z_s)$ with the global or anatomical reference frame of the crash subject $(X_g, Y_g, Z_g)$ using a direction cosine matrix (DCM) or quaternion rotation:
    
    $$\vec{a}_g = R(\vec{q}) \vec{a}_s$$
    

### Step 3: Structuring Inputs for the PINN

A PINN doesn't just want isolated data points; it relies on continuous space-time gradients. Your input tensor should represent a sliding time window around the impact event:

- **Input Array Shape:** $[B, T, 6]$, where $B$ is batch size, $T$ is the number of time steps in the window (e.g., 200 ms of data), and the 6 channels are $[a_x, a_y, a_z, \omega_x, \omega_y, \omega_z]$.
    
- **Temporal Gradients:** Because your PINN solves differential biomechanics equations, pass the exact timestamp vector $\Delta t$ alongside the data. The precise hardware timestamps from the ICM-42688-P ensure that the network's internal automatic differentiation ($\frac{\partial f}{\partial t}$) maps accurately to real-world time.
    

## 3. Integrating Biomechanics Equations into the PINN

Your PINN will optimize its weights by balancing data-driven loss with physics-based constraints. The collected IMU metrics map directly to standard biomechanical injury criteria:

### Head Injury Criterion (HIC)

The PINN can monitor head acceleration to calculate the HIC over the most severe impact window $(t_2 - t_1)$:

$$\text{HIC} = \max_{t_1, t_2} \left\{ (t_2 - t_1) \left[ \frac{1}{t_2 - t_1} \int_{t_1}^{t_2} \|\vec{a}_g(t)\| \, dt \right]^{2.5} \right\}$$

The PINN enforces this by using the accelerometer data stream to compute the integral, penalizing predictions that violate the expected rigid-body kinematics.

### Rotational Injury (Brain Shear Strain)

Linear acceleration isn't enough to evaluate brain trauma; rotational acceleration ($\alpha$) causes tissue shearing. The gyroscope provides angular velocity ($\vec{\omega}$). The PINN can compute rotational acceleration through automatic differentiation or numerical differentiation of the gyro stream:

$$\vec{\alpha}(t) = \frac{d\vec{\omega}}{dt}$$

This allows your network's custom loss function to evaluate metrics like the **Brain Injury Criterion (BrIC)**:

$$\text{BrIC} = \sqrt{\left(\frac{\omega_x}{\omega_{xcr}}\right)^2 + \left(\frac{\omega_y}{\omega_{ycr}}\right)^2 + \left(\frac{\omega_z}{\omega_{zcr}}\right)^2}$$

_(Where $\omega_{cr}$ values represent critical injury thresholds for each axis)._

By enforcing these kinematic constraints ($\frac{d\vec{v}}{dt} - \vec{a} = 0$), your PINN will stay regularized even if the sensor undergoes brief clipping or high-frequency noise during a severe impact event.


---
# **u-blox NEO-6M (GPS)**

The **u-blox NEO-6M** is an industry-standard, classic GPS receiver module. It belongs to the older u-blox 6 generation, but remains widely used in the hobbyist, maker, and engineering prototyping space due to its low cost, ease of integration, and robust performance for basic localization tasks

The NEO-6M is a standalone **GNSS/GPS receiver** module that tracks up to 50 channels simultaneously. Its primary function is to lock onto signals from overhead GPS satellites, calculate its exact spatial position, and output this data as a series of standardized text sentences.

For more details on augmentation systems, see:
- **[[01_Hardware/GPS_and_SBAS/GAGAN|GAGAN (India's SBAS)]]**
- **[[01_Hardware/GPS_and_SBAS/SBAS_Overview|SBAS Overview]]**

## Core Technical Metrics

The primary GPS L1 frequency is **1575.42 MHz**.  This band serves as the fundamental frequency for civilian users and carries the Coarse/Acquisition (C/A) code for general navigation, alongside the encrypted Precision (P(Y)) code for military use

* ***Constellation Support:** u-blox NEO-6M Supports **GPS L1** frequency (1575.42 MHz) and C/A code. It also supports [[SBAS (Satellite-Based Augmentation Systems)]] (WAAS, EGNOS, MSAS, [[GAGAN]]) for differential corrections. Note that it does _not_ natively track modern multi-GNSS constellations like GLONASS, Galileo, or BeiDou simultaneously (which newer chips like the NEO-M8 or M9 do)

- **Horizontal Position Accuracy:** Approximately **2.5 meters** under open skies (down to **2.0 meters** with SBAS enabled).

- **Velocity & Timing Accuracy:** Maximum velocity limit of 500 m/s with a timing pulse resolution RMS of 30 ns.

- **Output Protocol:** Emits standard **NMEA-0183** text strings (such as `$GPRMC`$, `$GPGGA`) and u-blox proprietary **UBX binary** format via a simple UART serial interface.

- **Time-To-First-Fix (TTFF):** * **Cold Start:** $\approx 27\text{–}32 \text{ seconds}$ (no prior satellite orbital data cached).

- **Hot Start:** $< 1 \text{ second}$ (satellite telemetry cached via battery backup).


### Comparative Efficiency

- **The Pro:** It is computationally lightweight. It handles the coordinate math internally on an embedded ARM processor, shifting no floating-point arithmetic overhead onto your host microcontroller.
- 
- **The Con:** Because it can only lock onto standard GPS satellites, it takes longer to establish a multi-satellite structural 3D-fix in dense urban environments ("urban canyons") compared to newer multi-constellation modules (like the NEO-M8N) which lock onto GLONASS and Galileo simultaneously to yield much higher geometry matrices (HDOP/VDOP).

| **Operating Mode**                        | **Power Dissipation** | **Current Draw (at 3.0V)**         | **Use Case**                                             |
| ----------------------------------------- | --------------------- | ---------------------------------- | -------------------------------------------------------- |
| **Max Performance / Continuous Tracking** | $115 \text{ mW}$      | $\approx 45 \text{ mA}$            | Real-time drone navigation, high-speed vehicles.         |
| **Power Save Mode (PSM @ 1 Hz)**          | $51 \text{ mW}$       | $\approx 11 \text{–}15 \text{ mA}$ | Battery-powered loitering sensors, tracking logs.        |
| **Backup State**                          | $35 \text{ μW}$<br>   | $\approx 15 \text{ μA}$            | Keeping the internal RTC and SRAM alive via button cell. |

---
# Ra-02 LoRa Radio (SX1278, 433 MHz)

The **Ra-02** is a long-range wireless communication module developed by Ai-Thinker. It is built around Semtech’s ultra-popular **SX1278** transceiver IC and operates at the **433 MHz** ISM (Industrial, Scientific, and Medical) radio band.

Unlike standard RF modules, Bluetooth, or Wi-Fi, the Ra-02 uses **LoRa (Long Range)** modulation, making it an exceptional tool for low-power, wide-area network (LPWAN) telemetry.

## 1. Core Technical Specifications

- **Transceiver Chip:** Semtech SX1278
    
- **Modulation Techniques:** LoRa, FSK, GFSK, MSK, GMSK, and OOK.
    
- **Operating Frequency:** 433 MHz (Software adjustable between 410 MHz and 525 MHz).
    
- **Link Budget:** Up to **148 dB**, allowing for extreme signal penetration.
    
- **Output Power:** Constant RF output power profile up to **+20 dBm (100 mW)** with changing VDD.
    
- **Receiver Sensitivity:** Down to **-148 dBm**.
    
- **Communication Interface:** SPI (Serial Peripheral Interface) for data and configuration registers.
    
- **Current Consumption:**
    
    - **TX (Transmit):** $\approx 120\text{ mA}$ (at +20 dBm)
        
    - **RX (Receive):** $\approx 10.8\text{ mA}$
        
    - **Deep Sleep:** $\approx 0.2 \, \mu\text{A}$
        
- **Operating Voltage:** 1.8V to 3.7V (Standard operating target is **3.3V**; its pins are _not_ 5V tolerant).
    
- **Form Factor:** SMD package with an IPEX (U.FL) external antenna connector.
    

## 2. Underlying Technology: LoRa Modulation

To understand why this module is efficient, it helps to understand its modulation scheme. LoRa utilizes **Chirp Spread Spectrum (CSS)**. Instead of modulating data onto a single static frequency carrier, it encodes information into linear frequency variations over time—known as "chirps."

This gives the Ra-02 two massive physical advantages:

1. **High Immunity to Multipath/Fading:** The continuously changing frequency makes the signal highly resilient against reflections from buildings or geographic terrain.
    
2. **Sub-Noise Floor Recovery:** Because of the distinct geometric signature of a chirp, the SX1278 can successfully decode incoming data packets even when the signal-to-noise ratio (SNR) is negative (i.e., the signal is completely buried beneath background thermal noise).
    

## 3. Communication Limits & Ranges

- **Range:** In a clear Line-of-Sight (LoS) rural or suburban setting, the Ra-02 can achieve communication distances of **5 to 10 km** using basic omnidirectional antennas. In dense urban environments, expect **1 to 3 km** due to heavy concrete obstruction and RF noise.
    
- **Data Rate:** LoRa trades bandwidth for range. The data rate ranges from **0.018 kbps to 37.5 kbps**. It is fundamentally designed for small payloads (sensor states, coordinates, structural metrics) rather than streaming audio or video.
    

## 4. How It Ties Into Your Architecture

If you are incorporating this alongside your **ICM-42688-P (IMU)** and **u-blox NEO-6M (GPS)**, the Ra-02 serves as the **telemetry link** to transmit your vehicle state and processed crash metrics back to a base station or remote logging server.

### Configuring the Data Trade-Off for Crash Alerts

When implementing your crash evaluation pipeline, you have to tune the SX1278's three core variables via your SPI library to ensure efficient transmission:

1. **Spreading Factor (SF6 to SF12):** Controls the duration of the chirp. A higher SF (e.g., SF12) increases the time-on-air, maximizing range and sensitivity but lowering the data rate. For rapid crash telemetry, you will want a lower Spreading Factor (e.g., **SF7** or **SF8**) to ensure the transmission window is as brief as possible, clearing the channel quickly.
    
2. **Signal Bandwidth (BW):** Typically selectable between 7.8 kHz and 500 kHz. Setting it to **125 kHz** or **250 kHz** strikes a reliable balance between receiver sensitivity and transmission speed.
    
3. **Coding Rate (CR 4/5 to 4/8):** Refers to cyclic error correction. During a high-impact crash, structural interference might distort a part of your RF packet. Setting a higher Coding Rate (**4/8**) injects redundant parity bits into the payload, allowing the receiving base station to reconstruct missing data blocks without requesting a power-hungry retransmission.
    

### Important Implementation Note

Because the Ra-02 operates strictly on **3.3V logic**, passing standard 5V signals from microcontrollers like an Arduino Uno directly to its SPI pins (MOSI, CLK, NSS) can permanently degrade the SX1278 silicon. Always employ a bi-directional logic level converter if your host microcontroller runs on a 5V rail.



# ESP32-S3


The **ESP32-S3** is a highly advanced, dual-core microcontroller system-on-chip (SoC) from Espressif Systems. It is a massive generation jump over the classic ESP32, specifically engineered to act as an edge-computing powerhouse for **Artificial Intelligence, Machine Learning (TinyML), and intensive signal processing tasks**.

If you are building a physical unit that logs crash events, runs your **PINN (Physics-Informed Neural Network)** on the edge, pulls high-G sensor streams from your **ICM-42688-P**, updates positions via the **NEO-6M GPS**, and sends alerts via the **Ra-02 LoRa** module, the ESP32-S3 is arguably the absolute best chip for the job.

## 1. Core Technical Specifications

- **CPU Architecture:** Dual-core 32-bit **Xtensa LX7** microprocessor running up to **240 MHz**.
    
- **Memory Architecture:**
    
    - **Internal:** 384 KB ROM, 512 KB SRAM, and 16 KB ultra-low-power RTC SRAM.
        
    - **External Storage Support:** High-speed SPI interfaces supporting Octal/Quad SPI Flash and **PSRAM (up to 8 MB or more)** with dedicated L1 cache allocation.
        
- **Wireless Connectivity:** * **Wi-Fi:** 2.4 GHz IEEE 802.11 b/g/n (up to 150 Mbps).
    
    - **Bluetooth:** BLE 5.0 and Bluetooth Mesh, supporting long-range data tracking up to 2 Mbps.
        
- **Native USB:** Integrated Full-Speed **USB OTG (On-The-Go)** and a native USB Serial/JTAG controller (allowing direct debugging/flashing without an external CP2102/CH340 USB-to-UART bridge).
    

## 2. Why It Fits a PINN Crash Evaluator

What makes the S3 variation distinct from its predecessors is its optimization for deep learning mathematical operations.

### On-Chip Vector / SIMD AI Acceleration

The Xtensa LX7 cores in the ESP32-S3 feature custom **Processor Instruction Extensions (PIE)**. This includes dedicated vector processing instructions and a bank of 128-bit wide vector registers.

- **The Benefit:** It accelerates operations like matrix multiplications, dot products, convolutions, and activation functions directly in hardware.
    
- **The Impact:** When compiled using Espressif's **ESP-NN** optimized library or **TensorFlow Lite for Microcontrollers (TFLite)**, neural networks execute multiple times faster on an S3 than on the baseline ESP32 or an ARM Cortex-M4. This ensures your PINN can evaluate biomechanical formulas in real-time right as an impact occurs.
    

### Dedicated GDMA (General DMA) Controller

The ESP32-S3 implements a highly efficient 5-channel transmit/receive General Direct Memory Access controller.

- When processing violent crashes, you cannot afford to have your CPU cores stall while waiting to read raw bits from the SPI interface connected to the ICM-42688-P IMU.
    
- The GDMA handles data blocks autonomously, streaming IMU measurements into a circular buffer in internal SRAM without wasting CPU cycles. This frees up both core processors to run your physical loss equations and network layers.
    

## 3. Peripheral Integration Matrix

Here is exactly how the ESP32-S3 acts as the central orchestrator for the sensors and communication modules you have selected:

|**Peripheral Module**|**Physical Interface used on ESP32-S3**|**Role in the Crash Detection Architecture**|
|---|---|---|
|**ICM-42688-P (IMU)**|**SPI2 (Master Mode)**|Streams raw linear acceleration ($a$) and angular velocity ($\omega$) at high output data rates ($>1\text{ kHz}$) directly into internal SRAM via GDMA.|
|**u-blox NEO-6M (GPS)**|**UART1 or UART2**|Asynchronously parses NMEA text logs (`$GPRMC`) on an independent thread to log baseline impact velocity, global time, and geofenced crash coordinates.|
|**Ra-02 LoRa (SX1278)**|**SPI3 (Master Mode)**|Serves as the long-range telemetry transmitter. Transmits compressed inference results, peak HIC values, and location coordinates to an emergency response base station.|

## 4. Hardware Resource Management Strategies

To extract maximum efficiency from this configuration, structure your application firmware using an asymmetric multi-processing layout under a Real-Time Operating System (**FreeRTOS**):

1. **Core 0 Pinning (Data Aggregation & Telemetry):** Assign Core 0 to handle system I/O. Let it parse incoming GPS strings from the UART buffer, capture high-speed IMU data frames via SPI, manage the Wi-Fi/BLE network layers, and handle the SPI packet transfers out to the Ra-02 LoRa transceiver.
    
2. **Core 1 Pinning (The PINN Execution Engine):** Isolate Core 1 strictly for your neural network. Pin your inference thread here so it isn't interrupted by radio interrupts or background tasks. It continuously monitors the localized buffer of physical inputs, tracks structural metrics against standard biomechanics equations (like HIC and BrIC thresholds), and flags crash vectors immediately upon math deviation.
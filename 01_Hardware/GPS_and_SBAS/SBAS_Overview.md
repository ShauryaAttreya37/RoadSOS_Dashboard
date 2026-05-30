
# SBAS (Satellite-Based Augmentation Systems)
**[[01_Hardware/Sensors_and_Chips|← Back to Hardware Stack]]**

**SBAS (Satellite-Based Augmentation Systems) are regional systems that improve GPS accuracy and reliability by broadcasting correction data via geostationary satellites. WAAS (USA), EGNOS (Europe), and MSAS (Japan) are examples of SBAS that the u-blox NEO-6M GPS module can use to enhance positioning performance.**

---

## 🌍 What is SBAS?

- **Definition:** Satellite-Based Augmentation System (SBAS) is a wide-area differential GPS correction system.
- **Purpose:** It improves accuracy, integrity, and availability of GPS signals by correcting errors caused by satellite orbit, clock drift, and ionospheric delays.
- **How it works:**
    - Ground reference stations monitor GPS signals.
    - Corrections are calculated and sent to geostationary satellites.
    - These satellites broadcast the corrected signals back to GPS receivers.
- **Accuracy:** Positioning errors can be reduced to **less than 1 meter** [GSSC](https://gssc.esa.int/navipedia/index.php?title=SBAS_General_Introduction) [SKYbrary Aviation Safety](https://skybrary.aero/articles/satellite-based-augmentation-system-sbas).

---

## ✈️ Key SBAS Systems Relevant to NEO-6M

| System    | Region             | Full Name                                         | Coverage                               | Notes                                                                                                                                                                                                                                                                          |
| --------- | ------------------ | ------------------------------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **WAAS**  | USA, North America | Wide Area Augmentation System                     | Continental US, Canada, Alaska, Mexico | First operational SBAS (2003). Widely used in aviation for precision approaches. [SKYbrary Aviation Safety](https://skybrary.aero/articles/satellite-based-augmentation-system-sbas)                                                                                           |
| **EGNOS** | Europe             | European Geostationary Navigation Overlay Service | Europe + parts of North Africa         | Provides corrections for GPS signals in Europe. Operational since 2009. [SKYbrary Aviation Safety](https://skybrary.aero/articles/satellite-based-augmentation-system-sbas)                                                                                                    |
| **MSAS**  | Japan              | Multi-functional Satellite Augmentation System    | Japan + nearby regions                 | Developed by Japan’s Civil Aviation Bureau. Supports aviation navigation. [SKYbrary Aviation Safety](https://skybrary.aero/articles/satellite-based-augmentation-system-sbas)                                                                                                  |
| GAGAN     | INDIA              | GPS Aided GEO Augmented Navigation                | India + Nearby Regions                 | GAGAN is India’s SBAS system, enhancing GPS accuracy and reliability for aviation and navigation. While it interoperates with WAAS, EGNOS, and MSAS, the u-blox NEO-6M does not support GAGAN, so upgrading to newer GNSS modules is the best way to benefit from it in India. |

---

## 📡 Why This Matters for u-blox NEO-6M

- The **NEO-6M GPS module** supports **GPS L1 frequency (1575.42 MHz)** and can use **SBAS corrections** (WAAS, EGNOS, MSAS).
- This means:
    - **Improved accuracy** compared to standalone GPS (from ~10 m down to ~1–2 m).
    - **Better reliability** for navigation applications like drones, robotics, and mapping.
- **Limitation:** It does _not_ support modern multi-GNSS (GLONASS, Galileo, BeiDou). For that, newer modules like **NEO-M8/M9** are required. [GSSC](https://gssc.esa.int/navipedia/index.php?title=SBAS_General_Introduction)

---

## ⚠️ Limitations & Considerations

- **Regional availability:** SBAS corrections only work within their coverage areas. For example, WAAS won’t help in India, but EGNOS signals may partially reach nearby regions.
- **Latency:** SBAS corrections are broadcast with slight delays, so they are best for navigation, not ultra-precise real-time applications.
- **Future systems:** India has its own SBAS called **[[GAGAN]] (GPS Aided GEO Augmented Navigation)**, which is not supported by NEO-6M but is available in newer GNSS modules. [GSSC](https://gssc.esa.int/navipedia/index.php?title=SBAS_General_Introduction)

---

✅ **In short:** SBAS systems like WAAS, EGNOS, and MSAS provide GPS correction data via satellites, improving accuracy and reliability. The NEO-6M can use these systems, but only within their regional coverage, and it lacks support for newer multi-GNSS constellations.
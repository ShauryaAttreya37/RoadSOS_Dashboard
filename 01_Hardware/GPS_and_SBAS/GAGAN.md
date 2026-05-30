# GAGAN (GPS Aided GEO Augmented Navigation)
**[[01_Hardware/Sensors_and_Chips|← Back to Hardware Stack]]**

**GAGAN (GPS Aided GEO Augmented Navigation) is India’s SBAS system, jointly developed by ISRO and the Airports Authority of India, designed to improve GPS accuracy and reliability for aviation and navigation across India and surrounding regions. It is interoperable with WAAS, EGNOS, and MSAS, but the u-blox NEO-6M module does not natively support GAGAN signals.**

---

## 🌍 What is GAGAN?

- **Full Name:** GPS Aided GEO Augmented Navigation
- **Developed by:** Indian Space Research Organisation (ISRO) + Airports Authority of India (AAI)
- **Purpose:** Provide satellite-based augmentation for GPS signals to meet **civil aviation safety-of-life requirements**.
- **Coverage:** Extends beyond India, reaching from **Africa to Australia**, making it one of the widest SBAS footprints globally.
- **Certification:** India became the **fourth country** (after USA, Europe, Japan) to establish a regional SBAS.

---

## ✈️ Key Features of GAGAN

- **Accuracy:** Provides GPS corrections to achieve **better than 1–2 meter accuracy**.
- **Integrity & Availability:** Ensures GPS signals are reliable enough for aviation, including precision approaches.
- **Unique Capability:** First SBAS certified to serve the **equatorial anomaly region**, using ISRO’s custom ionospheric correction algorithm (IGM-MLDF).
- **Infrastructure:**
    - 15 Indian Reference Stations (INRES)
    - 2 Master Control Centers (INMCC)
    - 3 Land Uplink Stations (INLUS)
    - 3 GEO satellites carrying GAGAN payloads (GSAT-8, GSAT-10, GSAT-15) [U R Rao Satellite Centre (URSC)](https://www.ursc.gov.in/navigation/gagan.jsp) [Indian Space Research Organisation](https://www.isro.gov.in/Navigation.html)

---

## 📡 Compatibility with u-blox NEO-6M

- The **NEO-6M GPS module** supports **SBAS corrections** (WAAS, EGNOS, MSAS).
- **Limitation:** It does _not_ list GAGAN as supported, since GAGAN was introduced later and requires newer GNSS chipsets.
- **Implication:** In India, the NEO-6M can still use GPS alone, but it won’t benefit from GAGAN’s corrections.
- **Alternative:** Newer modules like **u-blox NEO-M8/M9** support multi-GNSS (GPS, GLONASS, Galileo, BeiDou) and are more likely to integrate with GAGAN for improved accuracy.

---

## ⚠️ Risks & Considerations

- **Regional dependency:** GAGAN corrections are only useful within its footprint (India + nearby regions).
- **Hardware limitation:** Using NEO-6M in India means missing out on GAGAN’s accuracy improvements.
- **Future-proofing:** For drones, robotics, or precision agriculture in India, upgrading to a GNSS module that supports GAGAN or multi-GNSS is strongly recommended.

---

✅ **In summary:** GAGAN is India’s SBAS system, enhancing GPS accuracy and reliability for aviation and navigation. While it interoperates with WAAS, EGNOS, and MSAS, the u-blox NEO-6M does not support GAGAN, so upgrading to newer GNSS modules is the best way to benefit from it in India.
# Infrastructure Reliability & SLA Compliance Audit Report

**System**: `Cloud_MultiRegion_VPC`  
**Terminal Pair**: `Client_App` $\longleftrightarrow$ `DB_Primary_East`  
**Audit Status**: **EXACT (Exact Closed-Form Solution)**  
**Solver Technology**: SAT-Frontier Dual Cut Compilation & Weighted Model Counting  

---

## 1. Executive Summary & SLA Metrics

| Metric | Exact Value | Description |
| :--- | :--- | :--- |
| **Availability ($R$)** | **`99.999958%`** | Steady-state operational probability |
| **Unavailability ($Q$)** | **`0.000042%`** | Failure probability ($1 - R$) |
| **Exact Rational Fraction** | `39999983185816319076659958501/40000000000000000000000000000` | Exact mathematical reliability |
| **SLA Classification** | **Six Nines (>= 99.9999%)** | Industry standard classification |
| **Annual Downtime** | **`0.22 minutes`** (`0.00 hours`) | Expected outage duration per year |
| **Monthly Downtime** | **`0.02 minutes`** | Expected outage duration per month |

---

## 2. Infrastructure Vulnerability & Single Points of Failure

- **Total Inclusion-Minimal Cuts**: `12`  
- **Single Points of Failure (SPOFs)**: **`0`**  

> [!TIP]
> **Resilient Design**: Zero Single Points of Failure detected. All minimal cuts require $\ge 2$ simultaneous link failures.

### Top Critical Cut Vulnerabilities

| Cut Order | Vulnerable Components | Failure Probability | Mode |
| :--- | :--- | :--- | :--- |
| 2 | `Client_App<->Edge_Ingress_East + Client_App<->Edge_Ingress_West` | `2.500000e-07` | 2-Link Cut |
| 2 | `Client_App<->Edge_Ingress_East + Edge_Ingress_West<->TGW_Central` | `5.000000e-08` | 2-Link Cut |
| 2 | `Client_App<->Edge_Ingress_West + Edge_Ingress_East<->TGW_East` | `5.000000e-08` | 2-Link Cut |
| 2 | `TGW_East<->DB_Primary_East + DB_Primary_East<->DB_Standby_Central` | `5.000000e-08` | 2-Link Cut |
| 2 | `Edge_Ingress_East<->TGW_East + Edge_Ingress_West<->TGW_Central` | `1.000000e-08` | 2-Link Cut |
| 2 | `TGW_East<->DB_Primary_East + TGW_Central<->DB_Standby_Central` | `1.000000e-08` | 2-Link Cut |
| 3 | `Client_App<->Edge_Ingress_East + TGW_East<->TGW_Central + DB_Primary_East<->DB_Standby_Central` | `2.500000e-10` | 3-Link Cut |
| 3 | `Client_App<->Edge_Ingress_East + TGW_East<->TGW_Central + TGW_Central<->DB_Standby_Central` | `5.000000e-11` | 3-Link Cut |
| 3 | `Client_App<->Edge_Ingress_West + TGW_East<->TGW_Central + TGW_East<->DB_Primary_East` | `5.000000e-11` | 3-Link Cut |
| 3 | `Edge_Ingress_East<->TGW_East + TGW_East<->TGW_Central + DB_Primary_East<->DB_Standby_Central` | `5.000000e-11` | 3-Link Cut |

---

## 3. Component Criticality & Sensitivity Ranking (Birnbaum Index)

The Birnbaum Importance Index $I_B(e) = \frac{\partial R}{\partial p_e}$ measures the marginal improvement in overall system availability gained by reinforcing each individual link.

| Rank | Component Link | Component Availability | Birnbaum Criticality Index | Upgrade Priority |
| :--- | :--- | :--- | :--- | :--- |
| #1 | `TGW_East<->DB_Primary_East` | `99.99%` | **`0.000601`** | MODERATE |
| #2 | `Client_App<->Edge_Ingress_East` | `99.95%` | **`0.000600`** | MODERATE |
| #3 | `Edge_Ingress_East<->TGW_East` | `99.99%` | **`0.000600`** | MODERATE |
| #4 | `Client_App<->Edge_Ingress_West` | `99.95%` | **`0.000600`** | MODERATE |
| #5 | `Edge_Ingress_West<->TGW_Central` | `99.99%` | **`0.000600`** | MODERATE |
| #6 | `DB_Primary_East<->DB_Standby_Central` | `99.95%` | **`0.000101`** | MODERATE |
| #7 | `TGW_Central<->DB_Standby_Central` | `99.99%` | **`0.000101`** | MODERATE |
| #8 | `TGW_East<->TGW_Central` | `99.90%` | **`0.000000`** | MODERATE |

---

## 4. Computational Performance & Audit Provenance

- **Dual Cut Compilation Time**: `0.34 ms`
- **Exact WMC Solving Time**: `0.43 ms`
- **Total Audit Latency**: `5.00 ms`
- **Search Tree Explored**: `33 nodes`

*Audited by SAT-Frontier Enterprise Engine v0.2.3. Zero Monte Carlo sampling or approximation error.*


---

# Infrastructure Reliability & SLA Compliance Audit Report

**System**: `Transatlantic_Subsea_Optical_Mesh`  
**Terminal Pair**: `NewYork_PoP` $\longleftrightarrow$ `Frankfurt_DECIX`  
**Audit Status**: **EXACT (Exact Closed-Form Solution)**  
**Solver Technology**: SAT-Frontier Dual Cut Compilation & Weighted Model Counting  

---

## 1. Executive Summary & SLA Metrics

| Metric | Exact Value | Description |
| :--- | :--- | :--- |
| **Availability ($R$)** | **`99.998976%`** | Steady-state operational probability |
| **Unavailability ($Q$)** | **`0.001024%`** | Failure probability ($1 - R$) |
| **Exact Rational Fraction** | `1999979517020513893118946009/2000000000000000000000000000` | Exact mathematical reliability |
| **SLA Classification** | **Four Nines (>= 99.99%)** | Industry standard classification |
| **Annual Downtime** | **`5.38 minutes`** (`0.09 hours`) | Expected outage duration per year |
| **Monthly Downtime** | **`0.45 minutes`** | Expected outage duration per month |

---

## 2. Infrastructure Vulnerability & Single Points of Failure

- **Total Inclusion-Minimal Cuts**: `12`  
- **Single Points of Failure (SPOFs)**: **`0`**  

> [!TIP]
> **Resilient Design**: Zero Single Points of Failure detected. All minimal cuts require $\ge 2$ simultaneous link failures.

### Top Critical Cut Vulnerabilities

| Cut Order | Vulnerable Components | Failure Probability | Mode |
| :--- | :--- | :--- | :--- |
| 2 | `NewYork_PoP<->Bude_MAREA_Cable + Halifax_CableStation<->Dublin_CableStation` | `6.000000e-06` | 2-Link Cut |
| 2 | `NewYork_PoP<->Halifax_CableStation + NewYork_PoP<->Bude_MAREA_Cable` | `2.000000e-06` | 2-Link Cut |
| 2 | `NewYork_PoP<->Bude_MAREA_Cable + Dublin_CableStation<->London_Telehouse` | `2.000000e-06` | 2-Link Cut |
| 2 | `London_Telehouse<->Frankfurt_DECIX + Paris_Interxion<->Frankfurt_DECIX` | `2.500000e-07` | 2-Link Cut |
| 3 | `Halifax_CableStation<->Dublin_CableStation + Bude_MAREA_Cable<->London_Telehouse + Bude_MAREA_Cable<->Paris_Interxion` | `3.000000e-09` | 3-Link Cut |
| 3 | `NewYork_PoP<->Halifax_CableStation + Bude_MAREA_Cable<->London_Telehouse + Bude_MAREA_Cable<->Paris_Interxion` | `1.000000e-09` | 3-Link Cut |
| 3 | `Bude_MAREA_Cable<->London_Telehouse + Dublin_CableStation<->London_Telehouse + Bude_MAREA_Cable<->Paris_Interxion` | `1.000000e-09` | 3-Link Cut |
| 3 | `Bude_MAREA_Cable<->Paris_Interxion + London_Telehouse<->Frankfurt_DECIX + London_Telehouse<->Paris_Interxion` | `5.000000e-10` | 3-Link Cut |
| 4 | `Halifax_CableStation<->Dublin_CableStation + Bude_MAREA_Cable<->London_Telehouse + Paris_Interxion<->Frankfurt_DECIX + London_Telehouse<->Paris_Interxion` | `1.500000e-12` | 4-Link Cut |
| 4 | `NewYork_PoP<->Bude_MAREA_Cable + Bude_MAREA_Cable<->London_Telehouse + London_Telehouse<->Frankfurt_DECIX + London_Telehouse<->Paris_Interxion` | `1.000000e-12` | 4-Link Cut |

---

## 3. Component Criticality & Sensitivity Ranking (Birnbaum Index)

The Birnbaum Importance Index $I_B(e) = \frac{\partial R}{\partial p_e}$ measures the marginal improvement in overall system availability gained by reinforcing each individual link.

| Rank | Component Link | Component Availability | Birnbaum Criticality Index | Upgrade Priority |
| :--- | :--- | :--- | :--- | :--- |
| #1 | `NewYork_PoP<->Bude_MAREA_Cable` | `99.80%` | **`0.004993`** | MODERATE |
| #2 | `Halifax_CableStation<->Dublin_CableStation` | `99.70%` | **`0.001997`** | MODERATE |
| #3 | `NewYork_PoP<->Halifax_CableStation` | `99.90%` | **`0.001993`** | MODERATE |
| #4 | `Dublin_CableStation<->London_Telehouse` | `99.90%` | **`0.001993`** | MODERATE |
| #5 | `London_Telehouse<->Frankfurt_DECIX` | `99.95%` | **`0.000501`** | MODERATE |
| #6 | `Paris_Interxion<->Frankfurt_DECIX` | `99.95%` | **`0.000500`** | MODERATE |
| #7 | `Bude_MAREA_Cable<->Paris_Interxion` | `99.90%` | **`0.000005`** | MODERATE |
| #8 | `Bude_MAREA_Cable<->London_Telehouse` | `99.90%` | **`0.000005`** | MODERATE |
| #9 | `London_Telehouse<->Paris_Interxion` | `99.90%` | **`0.000001`** | MODERATE |

---

## 4. Computational Performance & Audit Provenance

- **Dual Cut Compilation Time**: `0.13 ms`
- **Exact WMC Solving Time**: `0.29 ms`
- **Total Audit Latency**: `6.38 ms`
- **Search Tree Explored**: `42 nodes`

*Audited by SAT-Frontier Enterprise Engine v0.2.3. Zero Monte Carlo sampling or approximation error.*


---

# Infrastructure Reliability & SLA Compliance Audit Report

**System**: `IEEE_14Bus_Transmission_Grid`  
**Terminal Pair**: `Bus_1` $\longleftrightarrow$ `Bus_14`  
**Audit Status**: **EXACT (Exact Closed-Form Solution)**  
**Solver Technology**: SAT-Frontier Dual Cut Compilation & Weighted Model Counting  

---

## 1. Executive Summary & SLA Metrics

| Metric | Exact Value | Description |
| :--- | :--- | :--- |
| **Availability ($R$)** | **`99.994957%`** | Steady-state operational probability |
| **Unavailability ($Q$)** | **`0.005043%`** | Failure probability ($1 - R$) |
| **Exact Rational Fraction** | `409579345092422661073377216169432029868350803/409600000000000000000000000000000000000000000` | Exact mathematical reliability |
| **SLA Classification** | **Four Nines (>= 99.99%)** | Industry standard classification |
| **Annual Downtime** | **`26.50 minutes`** (`0.44 hours`) | Expected outage duration per year |
| **Monthly Downtime** | **`2.21 minutes`** | Expected outage duration per month |

---

## 2. Infrastructure Vulnerability & Single Points of Failure

- **Total Inclusion-Minimal Cuts**: `64`  
- **Single Points of Failure (SPOFs)**: **`0`**  

> [!TIP]
> **Resilient Design**: Zero Single Points of Failure detected. All minimal cuts require $\ge 2$ simultaneous link failures.

### Top Critical Cut Vulnerabilities

| Cut Order | Vulnerable Components | Failure Probability | Mode |
| :--- | :--- | :--- | :--- |
| 2 | `Bus_1<->Bus_2 + Bus_1<->Bus_5` | `2.500000e-05` | 2-Link Cut |
| 2 | `Bus_9<->Bus_14 + Bus_13<->Bus_14` | `2.500000e-05` | 2-Link Cut |
| 3 | `Bus_6<->Bus_12 + Bus_6<->Bus_13 + Bus_9<->Bus_14` | `1.250000e-07` | 3-Link Cut |
| 3 | `Bus_6<->Bus_13 + Bus_9<->Bus_14 + Bus_12<->Bus_13` | `1.250000e-07` | 3-Link Cut |
| 3 | `Bus_5<->Bus_6 + Bus_6<->Bus_11 + Bus_9<->Bus_14` | `5.000000e-08` | 3-Link Cut |
| 3 | `Bus_5<->Bus_6 + Bus_9<->Bus_10 + Bus_9<->Bus_14` | `5.000000e-08` | 3-Link Cut |
| 3 | `Bus_5<->Bus_6 + Bus_9<->Bus_14 + Bus_10<->Bus_11` | `5.000000e-08` | 3-Link Cut |
| 3 | `Bus_4<->Bus_9 + Bus_5<->Bus_6 + Bus_7<->Bus_9` | `2.000000e-08` | 3-Link Cut |
| 3 | `Bus_4<->Bus_7 + Bus_4<->Bus_9 + Bus_5<->Bus_6` | `8.000000e-09` | 3-Link Cut |
| 4 | `Bus_1<->Bus_5 + Bus_2<->Bus_3 + Bus_2<->Bus_4 + Bus_2<->Bus_5` | `6.250000e-10` | 4-Link Cut |

---

## 3. Component Criticality & Sensitivity Ranking (Birnbaum Index)

The Birnbaum Importance Index $I_B(e) = \frac{\partial R}{\partial p_e}$ measures the marginal improvement in overall system availability gained by reinforcing each individual link.

| Rank | Component Link | Component Availability | Birnbaum Criticality Index | Upgrade Priority |
| :--- | :--- | :--- | :--- | :--- |
| #1 | `Bus_9<->Bus_14` | `99.50%` | **`0.005079`** | MODERATE |
| #2 | `Bus_1<->Bus_5` | `99.50%` | **`0.005000`** | MODERATE |
| #3 | `Bus_1<->Bus_2` | `99.50%` | **`0.005000`** | MODERATE |
| #4 | `Bus_13<->Bus_14` | `99.50%` | **`0.005000`** | MODERATE |
| #5 | `Bus_5<->Bus_6` | `99.80%` | **`0.000089`** | MODERATE |
| #6 | `Bus_6<->Bus_13` | `99.50%` | **`0.000050`** | MODERATE |
| #7 | `Bus_6<->Bus_12` | `99.50%` | **`0.000025`** | MODERATE |
| #8 | `Bus_12<->Bus_13` | `99.50%` | **`0.000025`** | MODERATE |
| #9 | `Bus_4<->Bus_9` | `99.80%` | **`0.000015`** | MODERATE |
| #10 | `Bus_6<->Bus_11` | `99.50%` | **`0.000010`** | MODERATE |

---

## 4. Computational Performance & Audit Provenance

- **Dual Cut Compilation Time**: `1.97 ms`
- **Exact WMC Solving Time**: `5.61 ms`
- **Total Audit Latency**: `227.59 ms`
- **Search Tree Explored**: `382 nodes`

*Audited by SAT-Frontier Enterprise Engine v0.2.3. Zero Monte Carlo sampling or approximation error.*


---

# Infrastructure Reliability & SLA Compliance Audit Report

**System**: `Avionics_DO178C_QuadRedundant_Actuator`  
**Terminal Pair**: `Pilot_Input` $\longleftrightarrow$ `Control_Surface`  
**Audit Status**: **EXACT (Exact Closed-Form Solution)**  
**Solver Technology**: SAT-Frontier Dual Cut Compilation & Weighted Model Counting  

---

## 1. Executive Summary & SLA Metrics

| Metric | Exact Value | Description |
| :--- | :--- | :--- |
| **Availability ($R$)** | **`100.000000%`** | Steady-state operational probability |
| **Unavailability ($Q$)** | **`0.000000%`** | Failure probability ($1 - R$) |
| **Exact Rational Fraction** | `1599999999828274748357958323691536247999/1600000000000000000000000000000000000000` | Exact mathematical reliability |
| **SLA Classification** | **Six Nines (>= 99.9999%)** | Industry standard classification |
| **Annual Downtime** | **`0.00 minutes`** (`0.00 hours`) | Expected outage duration per year |
| **Monthly Downtime** | **`0.00 minutes`** | Expected outage duration per month |

---

## 2. Infrastructure Vulnerability & Single Points of Failure

- **Total Inclusion-Minimal Cuts**: `36`  
- **Single Points of Failure (SPOFs)**: **`0`**  

> [!TIP]
> **Resilient Design**: Zero Single Points of Failure detected. All minimal cuts require $\ge 2$ simultaneous link failures.

### Top Critical Cut Vulnerabilities

| Cut Order | Vulnerable Components | Failure Probability | Mode |
| :--- | :--- | :--- | :--- |
| 2 | `Pilot_Input<->FCC_Primary + Pilot_Input<->FCC_Secondary` | `1.000000e-10` | 2-Link Cut |
| 2 | `Pilot_Input<->FCC_Primary + Actuator_B<->Control_Surface` | `0.000000e+00` | 2-Link Cut |
| 2 | `Pilot_Input<->FCC_Secondary + Actuator_A<->Control_Surface` | `0.000000e+00` | 2-Link Cut |
| 2 | `Actuator_A<->Control_Surface + Actuator_B<->Control_Surface` | `0.000000e+00` | 2-Link Cut |
| 3 | `Pilot_Input<->FCC_Primary + Bus_Controller_3<->Actuator_B + Bus_Controller_4<->Actuator_B` | `2.500000e-12` | 3-Link Cut |
| 3 | `Pilot_Input<->FCC_Secondary + Bus_Controller_1<->Actuator_A + Bus_Controller_2<->Actuator_A` | `2.500000e-12` | 3-Link Cut |
| 3 | `Pilot_Input<->FCC_Primary + FCC_Secondary<->Bus_Controller_3 + Bus_Controller_4<->Actuator_B` | `5.000000e-13` | 3-Link Cut |
| 3 | `Pilot_Input<->FCC_Primary + FCC_Secondary<->Bus_Controller_4 + Bus_Controller_3<->Actuator_B` | `5.000000e-13` | 3-Link Cut |
| 3 | `Pilot_Input<->FCC_Secondary + FCC_Primary<->Bus_Controller_1 + Bus_Controller_2<->Actuator_A` | `5.000000e-13` | 3-Link Cut |
| 3 | `Pilot_Input<->FCC_Secondary + FCC_Primary<->Bus_Controller_2 + Bus_Controller_1<->Actuator_A` | `5.000000e-13` | 3-Link Cut |

---

## 3. Component Criticality & Sensitivity Ranking (Birnbaum Index)

The Birnbaum Importance Index $I_B(e) = \frac{\partial R}{\partial p_e}$ measures the marginal improvement in overall system availability gained by reinforcing each individual link.

| Rank | Component Link | Component Availability | Birnbaum Criticality Index | Upgrade Priority |
| :--- | :--- | :--- | :--- | :--- |
| #1 | `Pilot_Input<->FCC_Primary` | `100.00%` | **`0.000010`** | MODERATE |
| #2 | `Pilot_Input<->FCC_Secondary` | `100.00%` | **`0.000010`** | MODERATE |
| #3 | `Actuator_A<->Control_Surface` | `100.00%` | **`0.000010`** | MODERATE |
| #4 | `Actuator_B<->Control_Surface` | `100.00%` | **`0.000010`** | MODERATE |
| #5 | `Bus_Controller_1<->Actuator_A` | `99.95%` | **`0.000000`** | MODERATE |
| #6 | `Bus_Controller_2<->Actuator_A` | `99.95%` | **`0.000000`** | MODERATE |
| #7 | `Bus_Controller_3<->Actuator_B` | `99.95%` | **`0.000000`** | MODERATE |
| #8 | `Bus_Controller_4<->Actuator_B` | `99.95%` | **`0.000000`** | MODERATE |
| #9 | `FCC_Primary<->Bus_Controller_1` | `99.99%` | **`0.000000`** | MODERATE |
| #10 | `FCC_Primary<->Bus_Controller_2` | `99.99%` | **`0.000000`** | MODERATE |

---

## 4. Computational Performance & Audit Provenance

- **Dual Cut Compilation Time**: `0.39 ms`
- **Exact WMC Solving Time**: `0.99 ms`
- **Total Audit Latency**: `26.32 ms`
- **Search Tree Explored**: `89 nodes`

*Audited by SAT-Frontier Enterprise Engine v0.2.3. Zero Monte Carlo sampling or approximation error.*


---

# Infrastructure Reliability & SLA Compliance Audit Report

**System**: `Telecom_Metro_DualRing_Optical`  
**Terminal Pair**: `CentralOffice_1` $\longleftrightarrow$ `CentralOffice_5`  
**Audit Status**: **EXACT (Exact Closed-Form Solution)**  
**Solver Technology**: SAT-Frontier Dual Cut Compilation & Weighted Model Counting  

---

## 1. Executive Summary & SLA Metrics

| Metric | Exact Value | Description |
| :--- | :--- | :--- |
| **Availability ($R$)** | **`99.993638%`** | Steady-state operational probability |
| **Unavailability ($Q$)** | **`0.006362%`** | Failure probability ($1 - R$) |
| **Exact Rational Fraction** | `3906001495756993003999/3906250000000000000000` | Exact mathematical reliability |
| **SLA Classification** | **Four Nines (>= 99.99%)** | Industry standard classification |
| **Annual Downtime** | **`33.44 minutes`** (`0.56 hours`) | Expected outage duration per year |
| **Monthly Downtime** | **`2.79 minutes`** | Expected outage duration per month |

---

## 2. Infrastructure Vulnerability & Single Points of Failure

- **Total Inclusion-Minimal Cuts**: `16`  
- **Single Points of Failure (SPOFs)**: **`0`**  

> [!TIP]
> **Resilient Design**: Zero Single Points of Failure detected. All minimal cuts require $\ge 2$ simultaneous link failures.

### Top Critical Cut Vulnerabilities

| Cut Order | Vulnerable Components | Failure Probability | Mode |
| :--- | :--- | :--- | :--- |
| 4 | `CentralOffice_2<->CentralOffice_1 + CentralOffice_2<->CentralOffice_1 + CentralOffice_6<->CentralOffice_5 + CentralOffice_6<->CentralOffice_5` | `1.600000e-11` | 4-Link Cut |
| 4 | `CentralOffice_2<->CentralOffice_1 + CentralOffice_2<->CentralOffice_1 + CentralOffice_7<->CentralOffice_6 + CentralOffice_7<->CentralOffice_6` | `1.600000e-11` | 4-Link Cut |
| 4 | `CentralOffice_2<->CentralOffice_1 + CentralOffice_2<->CentralOffice_1 + CentralOffice_8<->CentralOffice_7 + CentralOffice_8<->CentralOffice_7` | `1.600000e-11` | 4-Link Cut |
| 4 | `CentralOffice_2<->CentralOffice_1 + CentralOffice_2<->CentralOffice_1 + CentralOffice_1<->CentralOffice_8 + CentralOffice_1<->CentralOffice_8` | `1.600000e-11` | 4-Link Cut |
| 4 | `CentralOffice_3<->CentralOffice_2 + CentralOffice_3<->CentralOffice_2 + CentralOffice_6<->CentralOffice_5 + CentralOffice_6<->CentralOffice_5` | `1.600000e-11` | 4-Link Cut |
| 4 | `CentralOffice_3<->CentralOffice_2 + CentralOffice_3<->CentralOffice_2 + CentralOffice_7<->CentralOffice_6 + CentralOffice_7<->CentralOffice_6` | `1.600000e-11` | 4-Link Cut |
| 4 | `CentralOffice_3<->CentralOffice_2 + CentralOffice_3<->CentralOffice_2 + CentralOffice_8<->CentralOffice_7 + CentralOffice_8<->CentralOffice_7` | `1.600000e-11` | 4-Link Cut |
| 4 | `CentralOffice_3<->CentralOffice_2 + CentralOffice_3<->CentralOffice_2 + CentralOffice_1<->CentralOffice_8 + CentralOffice_1<->CentralOffice_8` | `1.600000e-11` | 4-Link Cut |
| 4 | `CentralOffice_4<->CentralOffice_3 + CentralOffice_4<->CentralOffice_3 + CentralOffice_6<->CentralOffice_5 + CentralOffice_6<->CentralOffice_5` | `1.600000e-11` | 4-Link Cut |
| 4 | `CentralOffice_4<->CentralOffice_3 + CentralOffice_4<->CentralOffice_3 + CentralOffice_7<->CentralOffice_6 + CentralOffice_7<->CentralOffice_6` | `1.600000e-11` | 4-Link Cut |

---

## 3. Component Criticality & Sensitivity Ranking (Birnbaum Index)

The Birnbaum Importance Index $I_B(e) = \frac{\partial R}{\partial p_e}$ measures the marginal improvement in overall system availability gained by reinforcing each individual link.

| Rank | Component Link | Component Availability | Birnbaum Criticality Index | Upgrade Priority |
| :--- | :--- | :--- | :--- | :--- |
| #1 | `CentralOffice_2<->CentralOffice_1` | `99.80%` | **`0.007928`** | MODERATE |
| #2 | `CentralOffice_3<->CentralOffice_2` | `99.80%` | **`0.007928`** | MODERATE |
| #3 | `CentralOffice_4<->CentralOffice_3` | `99.80%` | **`0.007928`** | MODERATE |
| #4 | `CentralOffice_5<->CentralOffice_4` | `99.80%` | **`0.007928`** | MODERATE |
| #5 | `CentralOffice_6<->CentralOffice_5` | `99.80%` | **`0.007928`** | MODERATE |
| #6 | `CentralOffice_7<->CentralOffice_6` | `99.80%` | **`0.007928`** | MODERATE |
| #7 | `CentralOffice_8<->CentralOffice_7` | `99.80%` | **`0.007928`** | MODERATE |
| #8 | `CentralOffice_1<->CentralOffice_8` | `99.80%` | **`0.007928`** | MODERATE |
| #9 | `CentralOffice_1<->CentralOffice_2` | `99.80%` | **`0.000000`** | MODERATE |
| #10 | `CentralOffice_2<->CentralOffice_3` | `99.80%` | **`0.000000`** | MODERATE |

---

## 4. Computational Performance & Audit Provenance

- **Dual Cut Compilation Time**: `0.17 ms`
- **Exact WMC Solving Time**: `0.18 ms`
- **Total Audit Latency**: `5.88 ms`
- **Search Tree Explored**: `25 nodes`

*Audited by SAT-Frontier Enterprise Engine v0.2.3. Zero Monte Carlo sampling or approximation error.*

---
name: rtos-firmware-development
description: Write deterministic, low-latency task schedulers and peripheral drivers for embedded FreeRTOS/Zephyr devices.
---

# RTOS Firmware Development

Implement deterministic, low-latency firmware tasks, peripheral drivers (SPI, I2C, UART, CAN), and memory protection routines for embedded microcontrollers (ARM Cortex-M, RISC-V, ESP32) using Real-Time Operating Systems (FreeRTOS, Zephyr RTOS, ThreadX).

The skill is **hardware-safe and contract-first**: task priorities, stack allocations, peripheral hardware registers, DMA buffers, and watchdog refresh windows are verified before implementation.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **🤖 Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context manifest below.
2. **💬 Non-Technical Mode (Plain English Prompts)**: If the user provides a natural language prompt (e.g. *"Implement a FreeRTOS SPI DMA sensor driver for STM32F4 with 5ms task rate and watchdog refresh"*), the agent **must automatically infer and populate** `target_mcu`, `rtos_kernel`, `task_spec`, `peripheral_spec`, and `memory_budget` from the user's text and repository configuration.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "RtosFirmwareContextManifest",
  "type": "object",
  "required": ["hardware_target", "firmware_spec"],
  "properties": {
    "hardware_target": {
      "type": "object",
      "required": ["mcu_architecture", "clock_frequency_mhz"],
      "properties": {
        "mcu_architecture": { "type": "string", "enum": ["cortex_m0", "cortex_m4f", "cortex_m7", "riscv32", "esp32s3"] },
        "clock_frequency_mhz": { "type": "integer" },
        "flash_size_kb": { "type": "integer" },
        "sram_size_kb": { "type": "integer" }
      }
    },
    "firmware_spec": {
      "type": "object",
      "required": ["rtos_kernel", "task_name", "priority"],
      "properties": {
        "rtos_kernel": { "type": "string", "enum": ["freertos", "zephyr", "threadx", "bare_metal"] },
        "task_name": { "type": "string", "pattern": "^[a-zA-Z0-9_-]+$" },
        "priority": { "type": "integer" },
        "stack_size_words": { "type": "integer", "default": 256 },
        "period_ms": { "type": "integer" }
      }
    },
    "peripheral_spec": {
      "type": "object",
      "required": ["bus_type"],
      "properties": {
        "bus_type": { "type": "string", "enum": ["spi", "i2c", "uart", "can", "gpio", "none"] },
        "use_dma": { "type": "boolean", "default": true },
        "timeout_ms": { "type": "integer", "default": 100 }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Safety Rules

If no raw JSON payload is provided, apply these defaults and safety checks:

- **`mcu_architecture`**: Extracted from CMake / Kconfig / `FreeRTOSConfig.h` or prompt keywords (e.g. "STM32F4" $\rightarrow$ `cortex_m4f`).
- **`rtos_kernel`**: Inferred from codebase imports (`#include "FreeRTOS.h"` $\rightarrow$ `freertos`, `#include <zephyr/kernel.h>` $\rightarrow$ `zephyr`).
- **`task_name`**: Derived from peripheral or feature name (e.g. `sensor_read_task`).
- **`priority`**: Assigned based on timing criticality (e.g. Motor control = High priority `5`, Status LED = Low priority `1`).
- **`bus_type`**: Extracted from prompt or peripheral datasheet specs.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: Context Ingestion & Hardware Discovery

1. Read `AGENTS.md`, `FreeRTOSConfig.h` / `prj.conf`, linker scripts (`.ld`), and target board definitions.
2. Inspect sibling driver implementations to inherit peripheral register abstractions, HAL conventions, and error codes.
3. Verify MCU memory budgets (Flash and SRAM limits) to prevent stack overflow or heap exhaustion.

### Step 2: Task Scheduler & Priority Design

1. Define task priority matrix preventing **Priority Inversion** (use Mutexes with Priority Inheritance `xSemaphoreCreateMutex()`, never plain binary semaphores for resource locking).
2. Allocate task stack bounds ensuring $\ge 20\%$ unused stack headroom ($Stack_{free} \ge 0.20 \times Stack_{total}$).
3. Enable task stack overflow checking (`#define configCHECK_FOR_STACK_OVERFLOW 2`).

### Step 3: Peripheral Driver Implementation

1. Implement non-blocking driver logic (Interrupt-driven or DMA transfers).
2. **I2C Bus Recovery Guard**: Add 9-clock manual GPIO pulse sequence to clear stuck `SDA` lines before bus initialization.
3. **SPI / DMA Cache Coherence**: Invalidate CPU Data Cache (`SCB_InvalidateDCache_by_Addr()`) around DMA buffers on Cortex-M7.
4. **UART / CAN Overrun Protection**: Implement atomic ring buffer pointers and handle FIFO overflow flags in ISR handlers (`FromISR` API variants).

### Step 4: Watchdog & System Protection

1. Enforce dedicated System Monitor task for Watchdog (WDT / IWDG) refreshes.
2. Verify all worker threads update heartbeat flags before the monitor task kicks the hardware watchdog.

### Step 5: Build Verification & Seam Testing

1. Compile firmware using the target cross-compiler (`arm-none-eabi-gcc`, `west build`, `ninja`).
2. Run memory section analysis (`arm-none-eabi-size`) to ensure `.text`, `.data`, and `.bss` fit within Flash/SRAM boundaries.

---

## 3. Reference Implementation: FreeRTOS SPI DMA Sensor Driver

```c
#include "FreeRTOS.h"
#include "task.h"
#include "semphr.h"
#include "stm32f4xx_hal.h"

/* 1. Context & Task Configurations */
#define SENSOR_TASK_STACK_SIZE   (512) // Words (2048 Bytes)
#define SENSOR_TASK_PRIORITY     (configMAX_PRIORITIES - 2)
#define SENSOR_READ_PERIOD_MS    (10)

static TaskHandle_t xSensorTaskHandle = NULL;
static SemaphoreHandle_t xSPIMutex = NULL;
static SemaphoreHandle_t xDMACompleteSem = NULL;
extern SPI_HandleTypeDef hspi1;

/* 2. DMA Interrupt Callback */
void HAL_SPI_TxRxCpltCallback(SPI_HandleTypeDef *hspi) {
    if (hspi->Instance == SPI1) {
        BaseType_t xHigherPriorityTaskWoken = pdFALSE;
        xSemaphoreGiveFromISR(xDMACompleteSem, &xHigherPriorityTaskWoken);
        portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
    }
}

/* 3. Deterministic Task Execution Loop */
void vSensorDriverTask(void *pvParameters) {
    TickType_t xLastWakeTime = xTaskGetTickCount();
    uint8_t txBuffer[6] = {0x80 | 0x28, 0, 0, 0, 0, 0}; // Read multi-byte command
    uint8_t rxBuffer[6] = {0};

    for (;;) {
        // Enforce deterministic execution period
        vTaskDelayUntil(&xLastWakeTime, pdMS_TO_TICKS(SENSOR_READ_PERIOD_MS));

        // Acquire SPI bus lock with priority inheritance
        if (xSemaphoreTake(xSPIMutex, pdMS_TO_TICKS(50)) == pdTRUE) {
            
            // Initiate non-blocking SPI DMA Transfer
            if (HAL_SPI_TransmitReceive_DMA(&hspi1, txBuffer, rxBuffer, 6) == HAL_OK) {
                
                // Wait for DMA completion interrupt with timeout safety
                if (xSemaphoreTake(xDMACompleteSem, pdMS_TO_TICKS(20)) == pdTRUE) {
                    // Process sensor readings
                    int16_t accelX = (int16_t)((rxBuffer[2] << 8) | rxBuffer[1]);
                    (void)accelX; // Consume sample
                } else {
                    // DMA Timeout: Abort transfer and reset peripheral
                    HAL_SPI_Abort(&hspi1);
                }
            }
            
            xSemaphoreGive(xSPIMutex);
        }
    }
}

/* 4. Driver Scaffolding & Initialization */
void vSensorDriverInit(void) {
    xSPIMutex = xSemaphoreCreateMutex();
    vSemaphoreCreateBinary(xDMACompleteSem);
    xSemaphoreTake(xDMACompleteSem, 0); // Start locked

    configASSERT(xSPIMutex != NULL);

    xTaskCreate(
        vSensorDriverTask,
        "SensorRead",
        SENSOR_TASK_STACK_SIZE,
        NULL,
        SENSOR_TASK_PRIORITY,
        &xSensorTaskHandle
    );
}
```

---

## 4. Latency, Task Jitter & Memory Safety Invariants

$$\text{Task Execution Jitter: } Jitter(t) = |t_{\text{actual\_wake}} - t_{\text{expected\_wake}}| \le 50 \, \mu\text{s}$$

$$\text{Stack Headroom Safety: } Stack_{\text{free\_bytes}} \ge 0.20 \times Stack_{\text{total\_bytes}}$$

$$\text{Flash Usage: } \text{Section}(.text) + \text{Section}(.rodata) + \text{Section}(.data) \le \text{Flash}_{\text{capacity}}$$

$$\text{SRAM Usage: } \text{Section}(.data) + \text{Section}(.bss) + \sum Stack_i + Heap_{\text{max}} \le 0.90 \times \text{SRAM}_{\text{capacity}}$$

---

## 5. Guardrails

### Operational Restrictions

- **Priority Inheritance Mandatory**: Always use Mutexes (`xSemaphoreCreateMutex()`) for shared peripheral locks; never use raw binary semaphores which cause priority inversion.
- **No Blocking Calls in ISRs**: Never call blocking RTOS functions (`vTaskDelay`, `xQueueReceive` without 0 timeout) inside Interrupt Service Routines.
- **Stack Overflow Hook Enabled**: Always configure stack overflow hooks (`configCHECK_FOR_STACK_OVERFLOW = 2`).

### Security & Hardware Invariants

- **DMA Cache Invalidation**: Always invalidate CPU data cache before reading DMA reception buffers on cached architectures (Cortex-M7).
- **I2C Bus Lockup Recovery**: Always implement manual 9-clock pulse sequences to clear stuck bus lines before initializing I2C peripherals.
- **Zero Unbounded Locks**: All semaphore/mutex acquisitions must specify explicit non-zero timeouts.

---

## 6. Atomic Failure Recovery & Rollback Handler

Before modifying firmware sources or linker scripts, capture git baseline state. If build or size compilation fails:

```bash
# Revert modified files
if [ -n "${MODIFIED_FILES:-}" ]; then
  git checkout -- ${MODIFIED_FILES} 2>/dev/null
fi

# Remove newly created files
if [ -n "${CREATED_FILES:-}" ]; then
  rm -rf ${CREATED_FILES} 2>/dev/null
fi
```

---

## 7. Verification Plan & Toolchain Commands

Execute cross-compilation and static analysis checks:

```bash
# 1. Compile firmware using target toolchain
arm-none-eabi-gcc -c -mcpu=cortex-m4 -mthumb -O2 -Wall -Wextra src/main.c -o build/main.o

# 2. Check section memory sizes
arm-none-eabi-size build/firmware.elf

# 3. For Zephyr RTOS projects
west build -b stm32f4_disc1 app
```

---

## 8. Completion Report

Report target MCU architecture, RTOS kernel version, tasks created with stack/priority metrics, memory usage breakdown (Flash & SRAM percentages), peripheral drivers implemented, build verification output, and safety audit results.

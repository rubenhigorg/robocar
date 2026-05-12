# Sistema de Control: Filtro de Kalman y PID

[← Volver al TFG2](README.md)

## Filtro de Kalman

### Fundamento

El filtro de Kalman estima el estado de un sistema dinámico a partir de mediciones ruidosas o incompletas. En este proyecto, estima la posición de los carriles cuando la detección visual es parcial o ausente.

**Asunciones:**
- Sistema lineal
- Ruido blanco (no correlacionado en el tiempo)
- Ruido de distribución gaussiana

**Ecuación de estado:**

```
x_t = A·x_{t-1} + B·u_t + w_t
```

Donde:
- `x_t` — Vector de estado (posición respecto al carril) en el tiempo t
- `A` — Matriz de transición de estados (nxn)
- `B` — Matriz de control (nxc)
- `u_t` — Vector de control (dirección)
- `w_t` — Ruido del proceso, N(0, Q)

### Operación en dos etapas

1. **Predicción:** Estima la posición del carril basándose en el modelo dinámico
2. **Corrección:** Ajusta la estimación con las mediciones reales del frame

### Implementación: Clase `Tracker`

Implementada en `src/robocar_pkg/lib/tracker.py`. Utiliza la librería `filterpy` para el filtro de Kalman y `numpy` para operaciones matemáticas.

**Parámetros del filtro:**

| Parámetro | Valor | Descripción |
|---|---|---|
| `dim_x` | 4 | Dimensiones del estado (posición y velocidad en 2D) |
| `dim_z` | 2 | Dimensiones de la medición (pendiente y x-intercept) |
| `x` | [0,0,0,0] | Estado inicial |
| `P` | Alta incertidumbre | Matriz de covarianza inicial |
| `Q` | Ruido blanco discreto | Covarianza del ruido del proceso |
| `R` | Valores bajos | Covarianza del ruido de medición (mediciones relativamente precisas) |
| `H` | Mapeo estado→medición | Matriz de función de medición |
| `F` | Dinámica del sistema | Matriz de transición de estado |

**Método `add(poly)`:**
1. `predict()` — Estima el estado actual
2. `update(measurement)` — Corrige con la nueva medición (polinomio con pendiente m e intercepto b)
3. Devuelve el polinomio filtrado que representa la línea estimada

### Utilidad práctica

El filtro de Kalman cumple dos funciones críticas:

- **Estimación ante detección ausente:** Cuando no se detecta un carril (ej. en curvas o cambios de luz), Kalman proporciona una estimación basada en los frames anteriores
- **Suavizado:** Elimina las fluctuaciones en las detecciones, proporcionando un seguimiento más estable y un control de dirección más suave

---

## Control PID

### Fundamento

PID (Proporcional-Integral-Derivativo) es un controlador en bucle cerrado que corrige el error entre la posición actual del robot y la posición deseada (centro del carril).

```
salida = P + I + D
```

Cada componente analiza el error desde una perspectiva temporal diferente:

| Componente | Perspectiva | Función |
|---|---|---|
| **P** (Proporcional) | Presente | Corrección proporcional al error actual |
| **I** (Integral) | Pasado | Acumula errores pasados para eliminar error constante |
| **D** (Derivativo) | Futuro | Anticipa cambios basándose en la tasa de variación del error |

### Respuesta Proporcional (P)

```
P = kp × error
```

- Error pequeño → corrección pequeña
- Error grande → corrección grande
- **Problema:** Sobre-impulso (overshooting) — el robot puede oscilar alrededor del centro del carril
- Si `kp` es demasiado alta, el sistema oscila continuamente

### Respuesta Integral (I)

```
I = I_anterior + ki × error × dt
```

- Acumula el error a lo largo del tiempo
- Incluso errores pequeños y constantes se corrigen eventualmente
- **Función principal:** Eliminar el error en estado estacionario (reducirlo a cero)

### Respuesta Derivativa (D)

```
D = kd × (error - error_anterior) / dt
```

- Proporcional a la tasa de cambio del error
- Si el error cambia rápido → respuesta grande (frena correcciones bruscas)
- **Función principal:** Reducir el sobre-impulso
- No afecta al error en estado estacionario
- Si `kd` es demasiado grande, el sistema se vuelve inestable por amplificar fluctuaciones normales

### Implementación

Las variables del controlador PID:

```python
# Constantes PID (a calibrar)
kp = ...  # Ganancia proporcional
ki = ...  # Ganancia integral
kd = ...  # Ganancia derivativa

# Variables de estado
sumError  = 0   # Acumulador integral
prevError = 0   # Error del frame anterior

# Para cada frame:
P = kp * averageError
I = sumError + averageError * ki * dt
D = (averageError - prevError) * kd / dt

angulo_giro = P + I + D

prevError = averageError
sumError = I
```

El ángulo de giro resultante se publica en el topic `/lane_info` y el `car_control_node` lo traduce a un valor PWM para el servomotor de dirección.

### Calibración

La calibración de las constantes PID (kp, ki, kd) es un proceso empírico que requiere ajuste mediante pruebas:

- **kp alto:** Respuesta rápida pero oscilante
- **ki alto:** Elimina offset pero puede causar inestabilidad
- **kd alto:** Suaviza pero puede amplificar ruido
- **El equilibrio óptimo** depende de las condiciones específicas (velocidad, circuito, iluminación)

import numpy as np
import matplotlib.pyplot as plt

def f(x):
    if x < -53:
        # Función cuadrática que tiende a 105 a medida que x disminuye
        return (105 * x - 10011.1929)/(x - 38.78125)
    elif -53 <= x < 0:
        return 170
    elif 0 <= x <= 53:
        return 40
    elif x > 53:
        # Función cuadrática que tiende a 105 a medida que x aumenta
        return (105 * x - 1904.0184)/(x + 38.3125)

# Vectorizar la función para que funcione con arrays de numpy
f_vectorized = np.vectorize(f)

# Crear un rango de valores x para mostrar la función
x_values = np.linspace(-1000, 1000, 400)
y_values = f_vectorized(x_values)

# Graficar la función
plt.plot(x_values, y_values, label='f(x)')
plt.axhline(y=105, color='r', linestyle='--', label='y = 105 (asymptote)')
plt.axvline(x=-53, color='g', linestyle='--', label='x = -53')
plt.axvline(x=53, color='g', linestyle='--', label='x = 53')
plt.xlabel('x')
plt.ylabel('f(x)')
plt.title('Piecewise Function with Quadratic Segments')
plt.legend()
#plt.show()
print(f(-10000.0))    
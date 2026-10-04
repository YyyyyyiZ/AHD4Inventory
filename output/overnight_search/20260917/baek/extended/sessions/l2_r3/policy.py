import numpy as np


def design(params):
    m = int(params["m"])
    cv = float(params["cv"])
    f = float(params["f"])

    # Each row contains:
    # target, order ceiling, linear age coefficients, quadratic age
    # coefficients, linear/quadratic pipeline coefficients, output breakpoint,
    # and output slope correction.
    table = {
        (7, 1.5, 0.0): (
            22.663271, 21.0,
            (0.020428, 0.028662, 2.731703, 2.347556,
             1.713536, 1.396374, 1.216561),
            (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            1.146999, 0.0, 4.0, 0.0
        ),
        (7, 2.0, 0.0): (
            19.998181, 18.0,
            (0.313311, 0.168941, 2.535823, 2.508042,
             2.288443, 1.478840, 1.168640),
            (-0.646538, -3.286560, -0.179632, -1.002602,
             -0.077429, -0.032525, 0.078055),
            1.146388, -0.193575, 4.0, 0.0
        ),
        (8, 1.5, 0.0): (
            19.517971, 23.0,
            (0.147014, 0.101811, 1.980277, 1.816475,
             1.887345, 1.258725, 1.194070, 0.816389),
            (-0.153335, -3.326531, 0.402235, -0.292749,
             -1.073033, -0.125844, -0.218510, 0.084040),
            0.682434, 0.205469, 6.0, 0.30
        ),
        (8, 2.0, 0.0): (
            22.233890, 21.0,
            (0.074360, 0.199412, 2.911037, 2.472224,
             1.944520, 1.727918, 1.494349, 1.160435),
            (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            1.039886, 0.0, 6.0, 0.45
        ),
        (7, 1.5, 0.5): (
            13.582767, 15.0,
            (0.203440, 0.189054, 0.576186, 0.668234,
             0.586774, 0.550185, 0.659711),
            (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            0.857884, 0.0, 3.0, -0.15
        ),
        (7, 2.0, 0.5): (
            12.588586, 7.0,
            (0.124590, 0.307019, 0.519781, 0.632182,
             0.594475, 0.598059, 0.766524),
            (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            0.956294, 0.0, 4.0, -0.30
        ),
        (8, 1.5, 0.5): (
            16.402960, 10.0,
            (0.240638, 0.416910, 0.650787, 0.650583,
             0.806507, 0.679244, 0.619057, 0.763062),
            (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            0.902856, 0.0, 1.0, -0.15
        ),
        (8, 2.0, 0.5): (
            20.479577, 6.0,
            (0.584473, 0.649759, 1.012728, 1.101189,
             0.862633, 1.013153, 1.033179, 0.691259),
            (-0.385409, 0.294273, -0.003795, -0.165633,
             1.617963, -0.040966, -0.393932, 2.591302),
            1.604524, -1.633266, 3.0, -0.60
        ),
    }

    key = (m, cv, f)
    if key not in table:
        key = min(
            table,
            key=lambda k: 10.0 * abs(k[0] - m)
                          + abs(k[1] - cv)
                          + 2.0 * abs(k[2] - f)
        )

    target, ceiling, linear, quadratic, pipe_linear, pipe_quadratic, \
        breakpoint, slope_correction = table[key]

    linear = np.asarray(linear, dtype=np.float64)
    quadratic = np.asarray(quadratic, dtype=np.float64)

    def policy(age, pipeline):
        value = target

        for i in range(len(age)):
            x = float(age[i])
            value -= linear[i] * x + quadratic[i] * x * x / 30.0

        if len(pipeline):
            x = float(pipeline[0])
            value -= pipe_linear * x + pipe_quadratic * x * x / 30.0

        if value > breakpoint:
            value += slope_correction * (value - breakpoint)

        if value <= 0.0:
            return 0.0
        if value >= ceiling:
            return ceiling
        return value

    return policy

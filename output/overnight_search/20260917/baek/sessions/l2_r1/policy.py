import numpy as np


def design(params):
    scenario = scenario_from_params(params)
    m = int(scenario.m)
    cv_code = int(round(2.0 * float(scenario.cv)))
    f_code = int(round(2.0 * float(scenario.f)))

    # Coefficients define:
    # q = intercept - pipeline_weight * pipeline[0]
    #               - dot(age_weights, age)
    coefficients = {
        (3, 3, 0): (8.8886, 0.9674, 0.0, 0.0, 0.8753),
        (3, 3, 1): (7.0300, 0.7220, 0.1530, 0.1254, 0.4284),
        (3, 4, 0): (8.6960, 1.0614, 0.0, 0.0, 1.1259),
        (3, 4, 1): (5.6629, 0.6146, 0.0527, 0.2253, 0.4047),

        (4, 3, 0): (13.2600, 1.1400, 0.0, 0.0, 1.5200, 1.1200),
        (4, 3, 1): (7.7233, 0.5150, 0.1029, 0.2478, 0.2918, 0.5336),
        (4, 4, 0): (11.2608, 1.1088, 0.0, 0.0, 1.4504, 1.1758),
        (4, 4, 1): (7.4797, 0.7652, 0.0891, 0.2826, 0.4185, 0.5222),

        (5, 3, 0): (15.4063, 1.0242, 0.0, 0.0, 1.8177, 1.4152, 1.1103),
        (5, 3, 1): (9.7485, 0.6727, 0.2093, 0.1971, 0.4761, 0.5081, 0.5266),
        (5, 4, 0): (14.3697, 1.1393, 0.0, 0.0, 1.8822, 1.6229, 1.2343),
        (5, 4, 1): (8.8721, 0.8445, 0.1662, 0.3087, 0.4041, 0.4648, 0.6294),
    }

    key = (m, cv_code, f_code)
    if key not in coefficients:
        compatible = [k for k in coefficients if k[0] == m]
        if not compatible:
            raise ValueError("Unsupported shelf life m")
        key = min(
            compatible,
            key=lambda k: abs(k[1] - cv_code) + 2.0 * abs(k[2] - f_code),
        )

    theta = np.asarray(coefficients[key], dtype=np.float64)
    intercept = float(theta[0])
    pipeline_weight = float(theta[1])
    age_weights = theta[2:].copy()
    age_weights.setflags(write=False)

    def policy(age, pipeline):
        q = intercept - pipeline_weight * float(pipeline[0])
        q -= float(np.dot(age_weights, age))
        return q

    return policy

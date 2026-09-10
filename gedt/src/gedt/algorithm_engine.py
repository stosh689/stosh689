class LinearTrend(EconomicAlgorithm):
    """
    Ordinary least-squares linear trend.

    Dependency-free implementation for the GEDT
    foundational algorithm layer.
    """

    name = "linear_trend"
    version = "1.0"

    def __init__(self) -> None:
        self._intercept = 0.0
        self._slope = 0.0
        self._sample_size = 0
        self._fitted = False

    def fit(
        self,
        data: Sequence[float],
    ) -> "LinearTrend":

        if len(data) < 2:
            raise ValueError(
                "linear trend requires at least two observations"
            )

        y = [float(value) for value in data]
        x = list(range(len(y)))

        x_mean = mean(x)
        y_mean = mean(y)

        numerator = sum(
            (xi - x_mean) * (yi - y_mean)
            for xi, yi in zip(x, y)
        )

        denominator = sum(
            (xi - x_mean) ** 2
            for xi in x
        )

        if denominator == 0:
            raise ValueError(
                "cannot calculate linear trend"
            )

        self._slope = numerator / denominator

        self._intercept = (
            y_mean
            - self._slope * x_mean
        )

        self._sample_size = len(y)
        self._fitted = True

        return self

    def predict(
        self,
        horizon: int = 1,
    ) -> list[float]:

        if not self._fitted:
            raise RuntimeError(
                "algorithm must be fitted before prediction"
            )

        if horizon < 1:
            raise ValueError(
                "horizon must be at least 1"
            )

        return [
            self._intercept
            + self._slope * (
                self._sample_size + i
            )
            for i in range(horizon)
        ]

    @property
    def slope(self) -> float:
        """Return fitted trend slope."""
        return self._slope

    @property
    def intercept(self) -> float:
        """Return fitted intercept."""
        return self._intercept

    @property
    def sample_size(self) -> int:
        """Return number of observations used for fitting."""
        return self._sample_size
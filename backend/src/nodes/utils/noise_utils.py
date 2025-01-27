from typing import Literal, Callable, List
import numpy as np

from .utils import get_h_w_c
from .image_utils import as_target_channels


def __add_noises(
    image: np.ndarray,
    noise_gen: Callable[[int, int], List[np.ndarray]],
    combine: Callable[[np.ndarray, List[np.ndarray]], np.ndarray],
) -> np.ndarray:
    img = image
    h, w, c = get_h_w_c(img)
    assert c != 2, "Noise cannot be added to 2-channel images."

    if c > 3:
        img = img[:, :, :3]

    noises = noise_gen(h, w)
    assert len(noises) > 0

    max_channels = min(c, 3)
    for n in noises:
        noise_channels = get_h_w_c(n)[2]
        assert noise_channels in (1, 3), "Noise must be a grayscale or RGB image."
        max_channels = max(max_channels, noise_channels)

    noises = [as_target_channels(n, max_channels) for n in noises]
    img = as_target_channels(img, max_channels)

    result = combine(img, noises)

    if c > 3:
        result = np.concatenate([result, image[:, :, 3:]], axis=2)

    return np.clip(result, 0, 1)


def __add_noise(
    image: np.ndarray,
    noise_gen: Callable[[int, int], np.ndarray],
    combine: Callable[[np.ndarray, np.ndarray], np.ndarray] = lambda i, n: i + n,
) -> np.ndarray:
    return __add_noises(
        image,
        lambda h, w: [noise_gen(h, w)],
        lambda i, n: combine(i, n[0]),
    )


NoiseType = Literal["gray", "rgb"]


# Applies gaussian noise to an image
def gaussian_noise(
    image: np.ndarray,
    amount: float,
    noise_type: NoiseType,
    seed: int = 0,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    noise_c = 3 if noise_type == "rgb" else 1
    return __add_noise(
        image,
        lambda h, w: rng.normal(0, amount, (h, w, noise_c)),
    )


# Applies uniform noise to an image
def uniform_noise(
    image: np.ndarray,
    amount: float,
    noise_type: NoiseType,
    seed: int = 0,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    noise_c = 3 if noise_type == "rgb" else 1
    return __add_noise(
        image,
        lambda h, w: rng.uniform(-amount, amount, (h, w, noise_c)),
    )


# Applies salt and pepper noise to an image
def salt_and_pepper_noise(
    image: np.ndarray,
    amount: float,
    noise_type: NoiseType,
    seed: int = 0,
) -> np.ndarray:
    def gen_noise(h: int, w: int):
        rng = np.random.default_rng(seed)
        noise_c = 3 if noise_type == "rgb" else 1
        amt = amount / 2
        pepper = rng.choice([0, 1], (h, w, noise_c), p=[amt, 1 - amt])
        salt = rng.choice([0, 1], (h, w, noise_c), p=[1 - amt, amt])
        return [pepper, salt]

    def combine(i: np.ndarray, n: List[np.ndarray]):
        pepper, salt = n
        return np.where(salt == 1, 1, np.where(pepper == 0, 0, i))

    return __add_noises(image, gen_noise, combine)


# Applies poisson noise to an image
def poisson_noise(
    image: np.ndarray,
    amount: float,
    noise_type: NoiseType,
    seed: int = 0,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    noise_c = 3 if noise_type == "rgb" else 1
    return __add_noise(
        image,
        lambda h, w: rng.poisson(amount, (h, w, noise_c)),
    )


# Applies speckle noise to an image
def speckle_noise(
    image: np.ndarray,
    amount: float,
    noise_type: NoiseType,
    seed: int = 0,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    noise_c = 3 if noise_type == "rgb" else 1
    return __add_noise(
        image,
        lambda h, w: rng.normal(0, amount, (h, w, noise_c)),
        lambda i, n: i + i * n,
    )

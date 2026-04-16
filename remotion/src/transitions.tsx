import { zoomBlur } from "./transitions/zoom-blur";

export { lightLeak } from "./transitions/light-leak";

// Чистый zoom без размытия (переиспользуем zoomBlur c blurAmount: 0).
export const zoomIn = () => zoomBlur({ direction: "in", blurAmount: 30, scaleAmount: 2 });
export const zoomOut = () => zoomBlur({ direction: "out", blurAmount: 30, scaleAmount: 2 });

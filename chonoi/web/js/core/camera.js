"use strict";
/* Camera ngang bám theo người chơi (cảnh lặn). Chỉ đổi chỗ nhìn, không đổi vị trí thật trong sim. */
(function (CN) {
  let camX = null;
  CN.camera = {
    // Trả về mép trái khung nhìn (đơn vị thế giới). Khung rộng hơn thế giới thì căn giữa.
    follow(targetX, viewW, minX, maxX) {
      const span = maxX - minX;
      if (viewW >= span) { camX = minX - (viewW - span) / 2; return camX; }
      const want = Math.max(minX, Math.min(maxX - viewW, targetX - viewW / 2));
      camX = camX === null ? want : camX + (want - camX) * 0.18;
      return camX;
    },
    reset() { camX = null; },
  };
})(window.CN);

// That's a neat trick
function trySpinning() {
  if (!config.RING_ANIMATION) {
    return;
  }

  if (lastRingPos === -1) {
    lastRingPos = gateStatus.ring_position;
  } else if (lastRingPos !== gateStatus.ring_position) {
    lastRingPos = gateStatus.ring_position;
    ring3.classList.add('rotating');
    ring3.classList.remove('slow-rotate');
    gateMoving = true;
  } else if (gateMoving) {
    gateMoving = false;
    stopSpinning(ring3);
  }
}

function stopSpinning(el) {
  // Step 1: Capture current computed transform (rotation)
  const computedStyle = window.getComputedStyle(el);
  const matrix = new DOMMatrixReadOnly(computedStyle.transform);

  // Calculate current rotation angle in degrees
  let angle = Math.atan2(matrix.b, matrix.a) * (180 / Math.PI);
  if (angle < 0) angle += 360;
  angle = angle % 360;

  // Step 2: Remove animation
  el.classList.remove('rotating');

  // Step 3: Apply current rotation as a static transform
  el.style.transform = `rotate(${angle}deg)`;

  // Force reflow to flush style changes
  void el.offsetWidth;

  // Step 4: Add transition and apply a final slow rotation
  el.classList.add('slow-rotate');

  // Rotate 10° more over 1s (simulate deceleration)
  el.style.transform = `rotate(${angle + 10}deg)`;

  // Optional cleanup after transition
  el.addEventListener(
    'transitionend',
    () => {
      el.classList.remove('slow-rotate');
      lastGateRotation = (angle + 10 + lastGateRotation) % 360;
      el.style.rotate = `${lastGateRotation}deg`;
      el.style.transform = '';
    },
    {once: true},
  );
}


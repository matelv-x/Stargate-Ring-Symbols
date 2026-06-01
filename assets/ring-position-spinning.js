// That's a neat trick
function trySpinning() {
  if (!config.RING_ANIMATION) {
    return;
  }

  if (gateStatus.ring_position === undefined || gateStatus.ring_position === null) {
    return;
  }

  let currentRingPos = Number(gateStatus.ring_position);

  if (!Number.isFinite(currentRingPos)) {
    return;
  }

  // When the gate is idle, show the visual ring parked at Earth / 12 o'clock.
  // This fixes refresh after an aborted/cleared dial where backend ring_position
  // may still contain the last physical motor position.
  if (shouldParkVisualRingAtHome()) {
    currentRingPos = VISUAL_HOME_RING_POSITION;
  }

  if (lastRingPos === -1) {
    lastRingPos = currentRingPos;
    gateMoving = false;
    setRingToPosition(currentRingPos, false);
    return;
  }

  if (lastRingPos !== currentRingPos) {
    lastRingPos = currentRingPos;
    gateMoving = true;
    setRingToPosition(currentRingPos, true);
    return;
  }

  if (gateMoving) {
    gateMoving = false;
    setRingToPosition(currentRingPos, true);
  }
}

function stopSpinning(el) {
  // Kept for compatibility with older custom code.
  // The ring no longer uses endless CSS spinning here.
  if (gateStatus.ring_position !== undefined && gateStatus.ring_position !== null) {
    const ringPosition = shouldParkVisualRingAtHome()
      ? VISUAL_HOME_RING_POSITION
      : gateStatus.ring_position;
    setRingToPosition(ringPosition, true);
  }
}

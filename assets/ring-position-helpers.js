// Backend Stargate logic:
// 1250 motor steps = one full visual ring revolution.
// ring_position 0 = Earth at Top Dead Center.
const RING_STEPS_PER_REVOLUTION = 1250;
const VISUAL_HOME_RING_POSITION = 0;
const RING_DEGREES_PER_SECOND = 120;

function normalizeDegrees(deg) {
  return ((deg % 360) + 360) % 360;
}

function ringPositionToDegrees(ringPosition) {
  const pos = Number(ringPosition);

  if (!Number.isFinite(pos)) {
    return lastGateRotation;
  }

  return normalizeDegrees((pos / RING_STEPS_PER_REVOLUTION) * 360);
}

function getStatusArray(name) {
  return Array.isArray(gateStatus[name]) ? gateStatus[name] : [];
}

function symbolIndexToRingPosition(symbolIndex) {
  const index = Number(symbolIndex);

  if (!Number.isFinite(index) || index < 1 || index > 39) {
    return null;
  }

  return (index - 1) * 32;
}

function getIncomingVisualRingPosition() {
  const incoming = getStatusArray('address_buffer_incoming');

  if (incoming.length === 0) {
    return null;
  }

  return symbolIndexToRingPosition(incoming[incoming.length - 1]);
}

function shouldParkVisualRingAtHome() {
  const noOutgoing = getStatusArray('address_buffer_outgoing').length === 0;
  let noIncoming = getStatusArray('address_buffer_incoming').length === 0;

  if (typeof hasIncomingBuffer === 'function') {
    noIncoming = !hasIncomingBuffer();
  }

  return (
    state === STATE_IDLE &&
    noOutgoing &&
    noIncoming &&
    !gateStatus.wormhole_active
  );
}

function setRingToPosition(ringPosition, animate = true) {
  const finalAngle = ringPositionToDegrees(ringPosition);

  ring3.classList.remove('rotating');
  ring3.classList.remove('slow-rotate');
  ring3.style.rotate = '';

  let currentAngle = lastGateRotation;

  let delta = finalAngle - currentAngle;

  // Use shortest path: -180° to +180°

  if (delta > 180) {

    delta -= 360;

  } else if (delta < -180) {

    delta += 360;

  }

  const targetAngle = currentAngle + delta;

  if (animate) {

    const degreesToTravel = Math.abs(delta);
    const durationSeconds = degreesToTravel / RING_DEGREES_PER_SECOND;

    ring3.style.transition = `transform ${durationSeconds}s linear`;
  } else {
    ring3.style.transition = 'none';
  }

  ring3.style.transform = `rotate(${targetAngle}deg)`;
  lastGateRotation = targetAngle;
}

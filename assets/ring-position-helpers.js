// Backend Stargate logic:
// 1250 motor steps = one full visual ring revolution.
// ring_position 0 = Earth at Top Dead Center.
const RING_STEPS_PER_REVOLUTION = 1250;
const VISUAL_HOME_RING_POSITION = 0;
const RING_MOTOR_MAX_DEGREES_PER_SECOND = 95;
const RING_MOTOR_ACCELERATION = 220;
const RING_ARRIVAL_EPSILON_DEGREES = 0.08;
const RING_ARRIVAL_EPSILON_VELOCITY = 1.2;

let visualRingAnimationFrame = null;
let visualRingVelocity = 0;
let visualRingTargetAngle = 0;
let visualRingLastFrameTime = null;

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

function shortestRingDelta(targetAngle, currentAngle) {
  return ((targetAngle - normalizeDegrees(currentAngle) + 540) % 360) - 180;
}

function stopVisualRingMotor() {
  if (visualRingAnimationFrame !== null) {
    window.cancelAnimationFrame(visualRingAnimationFrame);
    visualRingAnimationFrame = null;
  }

  visualRingLastFrameTime = null;
  visualRingVelocity = 0;
}

function setVisualRingAngle(angle) {
  ring3.style.transition = 'none';
  ring3.style.transform = `rotate(${angle}deg)`;
  lastGateRotation = angle;
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
    noIncoming
  );
}

function setRingToPosition(ringPosition, animate = true) {
  const finalAngle = ringPositionToDegrees(ringPosition);

  ring3.classList.remove('rotating');
  ring3.classList.remove('slow-rotate');
  ring3.style.rotate = '';

  const currentAngle = lastGateRotation;
  const delta = shortestRingDelta(finalAngle, currentAngle);
  const targetAngle = currentAngle + delta;

  visualRingTargetAngle = targetAngle;

  if (!animate || Math.abs(delta) <= RING_ARRIVAL_EPSILON_DEGREES) {
    stopVisualRingMotor();
    setVisualRingAngle(targetAngle);
    return;
  }

  if (visualRingAnimationFrame === null) {
    visualRingLastFrameTime = null;
    visualRingAnimationFrame = window.requestAnimationFrame(updateVisualRingMotor);
  }
}

function updateVisualRingMotor(timestamp) {
  if (visualRingLastFrameTime === null) {
    visualRingLastFrameTime = timestamp;
  }

  const dt = Math.min((timestamp - visualRingLastFrameTime) / 1000, 0.05);
  visualRingLastFrameTime = timestamp;

  const delta = visualRingTargetAngle - lastGateRotation;
  const distance = Math.abs(delta);
  const direction = Math.sign(delta) || 1;
  const speed = Math.abs(visualRingVelocity);

  if (
    distance <= RING_ARRIVAL_EPSILON_DEGREES &&
    speed <= RING_ARRIVAL_EPSILON_VELOCITY
  ) {
    setVisualRingAngle(visualRingTargetAngle);
    stopVisualRingMotor();
    return;
  }

  const stoppingDistance = (speed * speed) / (2 * RING_MOTOR_ACCELERATION);
  let accelerationDirection = direction;

  if (speed > RING_ARRIVAL_EPSILON_VELOCITY && Math.sign(visualRingVelocity) !== direction) {
    accelerationDirection = direction;
  } else if (stoppingDistance >= distance) {
    accelerationDirection = -Math.sign(visualRingVelocity || direction);
  }

  visualRingVelocity += accelerationDirection * RING_MOTOR_ACCELERATION * dt;

  if (Math.abs(visualRingVelocity) > RING_MOTOR_MAX_DEGREES_PER_SECOND) {
    visualRingVelocity = Math.sign(visualRingVelocity) * RING_MOTOR_MAX_DEGREES_PER_SECOND;
  }

  const nextAngle = lastGateRotation + visualRingVelocity * dt;
  const nextDelta = visualRingTargetAngle - nextAngle;

  if (Math.sign(nextDelta) !== direction && Math.abs(nextDelta) < 1.4) {
    setVisualRingAngle(visualRingTargetAngle);
    stopVisualRingMotor();
    return;
  }

  setVisualRingAngle(nextAngle);
  visualRingAnimationFrame = window.requestAnimationFrame(updateVisualRingMotor);
}

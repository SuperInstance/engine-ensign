# Pathos — The Presentation Layer

*How the dashboard feels. Colors that communicate. Sounds that don't panic.*

---

## The Principle

The captain is not a data scientist. The captain is a human being, standing at the helm in a pitching boat, possibly at 3 AM, possibly tired, possibly scared. The display must speak to that person — not to the engineer who designed it.

Every visual and auditory choice is a communication decision. The wrong color wastes attention. The wrong sound wastes composure. The wrong layout wastes time.

## Color Language

### Green = Normal
Not "good." Normal. The engine is doing what it should be doing. Green is the absence of concern. It should be muted enough that it doesn't demand attention — the captain should be able to look at a green display and think about something else.

We use `#00FF00` (pure green) in day mode, `#004400` (dark green) in night mode. The night green is almost invisible — by design. If everything is dark green, everything is fine.

### Yellow = Caution
Something has changed. It's not an emergency, but it's not normal either. The captain should *notice* yellow without being alarmed by it.

Yellow is `#FFFF00` in day mode, `#AAAA00` in night mode. The night yellow is dim enough to read without blowing out night vision but bright enough to catch the eye.

### Red = Critical
Act now. The engine is at risk. Red means "do something about this immediately."

Red is `#FF0000` in day mode, `#AA0000` in night mode. We avoid flashing — flashing induces panic. Steady red is authoritative. Flashing red is hysterical.

### Cyan = Accent
Used for non-critical information: labels, dial faces, decorative elements. Cyan (`#00FFFF` day, muted blue night) is neutral and doesn't conflict with the green/yellow/red severity system.

## Analog vs Digital

**Analog dials** for parameters where *trend* matters. The captain doesn't need to know that RPM is 2,347. He needs to know if it's *increasing* or *decreasing* and if the needle is in the green zone. Analog dials communicate trend through motion — the needle's position and direction of travel tell the whole story in a glance.

**Digital readouts** for parameters where *absolute value* matters. "12.3V" is meaningful. A dial showing battery voltage doesn't help — you need the number. Temperature and pressure are in between; we use bar gauges (which are a visual analog) plus digital readouts below them.

The Yanmar 7-inch layout uses analog dial for RPM, bar gauges for temp and oil pressure, digital readouts for volts/fuel/hours/rate. This is not arbitrary — it's based on what the captain actually looks at while underway.

## Night Mode Philosophy

Night mode is not "dim day mode." It's a different design paradigm.

1. **Red spectrum only.** Rod cells in the human eye aren't sensitive to red light. Dim red/orange display preserves dark-adapted night vision, which takes 20-30 minutes to fully develop and is destroyed by 1 second of white light.

2. **Larger text.** Pupil dilation at night makes small text harder to resolve. Increase font size by 20-30%.

3. **Less information.** Show only what's needed. On a dark bridge at 3 AM, the captain needs RPM, temp, and warnings. Fuel rate and engine hours can wait.

4. **No animation.** A gauge that sweeps or pulses is a light source that destroys night vision. Static values only.

## Sound Design

The buzzer is the most dangerous tool in the system. Used correctly, it saves the engine. Used incorrectly, it causes the captain to disable it.

### The Single Beep

When a new WARNING or CRITICAL alert triggers:
- One beep, 150ms duration, 2730 Hz
- Then silence for 5 seconds
- If condition persists or worsens, another beep
- Captain acknowledges → silence until condition changes

2730 Hz is piercing without being painful. It cuts through engine noise and wind noise. It's not a pleasant frequency — that's intentional. A pleasant alert is an ignorable alert.

### What Not To Do

- **No continuous buzzer.** A continuous buzzer induces panic and makes it impossible to think or communicate. The captain will disable it with a wire cutter.
- **No ascending tone sequences.** They sound like a bomb timer in a movie.
- **No voice synthesis.** The ESP32 can't do it well, and a robotic voice saying "WARNING: ENGINE OVERHEAT" is more confusing than a buzzer plus a screen readout.
- **No different tones for different alerts.** One tone, one meaning: "look at the screen." The screen tells you what's wrong.

## Alert Banner Design

The alert banner is a 30-pixel bar at the top of the display. It appears when there's an active alert and disappears when the condition clears.

- Background: solid red (critical) or yellow (warning)
- Text: white, centered, specific ("HIGH COOLANT TEMP" not "WARNING")
- Duration: persists until condition clears, even after acknowledgment
- No animation, no flashing, no pulsing

The banner is small enough that it doesn't obscure the gauges below it. But it's at the top — the first place the eye goes.

## The Dashboard as Conversation

The display is the agent speaking. Every pixel is a word. The captain reads the display the way you read a face — holistically, in less than a second.

A well-designed dashboard says: "Everything is fine. Here's the proof." Or: "Something is wrong. Here's what." It does not say: "Here are 47 data points; please analyze them."

The agent's job is to curate. Show what matters. Hide what doesn't. Escalate visually when conditions change. The display should feel like a competent first mate glancing over and giving a thumbs up — or catching your eye with concern.

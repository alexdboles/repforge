"""UI contract checks, not microphone/browser-quality claims. Browser checked at release gate."""
from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[2] / 'frontend' / 'src'


def test_public_sample_and_honest_metrics():
    sample = (FRONTEND / 'pages/SampleReport.tsx').read_text()
    assert '<Navigate' not in sample
    assert 'Listening IQ' not in sample and 'sample-replay-cue' not in sample
    assert 'toast.info' not in sample and 'v: "38s"' not in sample
    assert 'Fictional illustrative values' in sample


def test_demo_primary_and_accessibility_contract():
    landing = (FRONTEND / 'pages/Landing.tsx').read_text()
    assert 'landing-demo-button' in landing and 'landing-sample-report' in landing
    assert 'Example simulation' in landing and 'Unlimited reps' not in landing
    assert 'auth-email-label' in landing and 'auth-password-label' in landing
    css = (FRONTEND / 'index.css').read_text()
    assert 'prefers-reduced-motion' in css and '@media print' in css
    assert 'FICTIONAL SAMPLE' in css


def test_setup_and_active_input_boundaries():
    simulation = (FRONTEND / 'pages/Simulation.tsx').read_text()
    mic = (FRONTEND / 'components/MicCheck.tsx').read_text()
    voice = (FRONTEND / 'lib/voice.ts').read_text()
    assert "sim?.status !== 'active'" in simulation and '!e.repeat' in simulation
    assert 'mic-check-typed' in mic and 'audio-confirm-yes' in mic
    assert 'stream.getTracks().forEach(t => t.stop())' in mic
    assert 'if (recRef.current !== rec) return;' in voice
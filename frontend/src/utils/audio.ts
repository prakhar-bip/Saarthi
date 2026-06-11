"use client";

class AudioEngine {
  private ctx: AudioContext | null = null;
  private muted: boolean = false;

  constructor() {
    // Check if window is defined (SSR safety)
    if (typeof window !== "undefined") {
      const isMutedStorage = localStorage.getItem("sarthi_audio_muted");
      this.muted = isMutedStorage === "true";
    }
  }

  private init() {
    if (!this.ctx && typeof window !== "undefined") {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === "suspended") {
      this.ctx.resume();
    }
  }

  toggleMute(): boolean {
    this.muted = !this.muted;
    if (typeof window !== "undefined") {
      localStorage.setItem("sarthi_audio_muted", this.muted ? "true" : "false");
    }
    return this.muted;
  }

  isMuted(): boolean {
    return this.muted;
  }

  playClick() {
    if (this.muted) return;
    this.init();
    if (!this.ctx) return;
    try {
      const t = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      
      osc.type = "sine";
      osc.frequency.setValueAtTime(1200, t);
      osc.frequency.exponentialRampToValueAtTime(300, t + 0.04);
      
      gain.gain.setValueAtTime(0.015, t);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.04);
      
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      
      osc.start(t);
      osc.stop(t + 0.05);
    } catch (e) {
      console.warn("Audio click play failed", e);
    }
  }

  playSuccess() {
    if (this.muted) return;
    this.init();
    if (!this.ctx) return;
    try {
      const t = this.ctx.currentTime;
      // Pentatonic ascending chord sweep (C4, E4, G4, A4, C5)
      const freqs = [261.63, 329.63, 392.00, 440.00, 523.25];
      freqs.forEach((f, index) => {
        const delay = index * 0.12;
        const osc = this.ctx!.createOscillator();
        const gain = this.ctx!.createGain();
        
        osc.type = "sine";
        osc.frequency.setValueAtTime(f, t + delay);
        
        gain.gain.setValueAtTime(0, t);
        gain.gain.linearRampToValueAtTime(0.08, t + delay + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.0001, t + delay + 1.2);
        
        osc.connect(gain);
        gain.connect(this.ctx!.destination);
        
        osc.start(t + delay);
        osc.stop(t + delay + 1.5);
      });
    } catch (e) {
      console.warn("Audio success play failed", e);
    }
  }

  playFailure() {
    if (this.muted) return;
    this.init();
    if (!this.ctx) return;
    try {
      const t = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(180, t);
      osc.frequency.linearRampToValueAtTime(90, t + 0.6);
      
      gain.gain.setValueAtTime(0.06, t);
      gain.gain.linearRampToValueAtTime(0.0001, t + 0.6);
      
      // Lowpass filter to make it warmer/deeper
      const filter = this.ctx.createBiquadFilter();
      filter.type = "lowpass";
      filter.frequency.setValueAtTime(300, t);
      
      osc.connect(filter);
      filter.connect(gain);
      gain.connect(this.ctx.destination);
      
      osc.start(t);
      osc.stop(t + 0.7);
    } catch (e) {
      console.warn("Audio failure play failed", e);
    }
  }

  playMilestone() {
    if (this.muted) return;
    this.init();
    if (!this.ctx) return;
    try {
      const t = this.ctx.currentTime;
      // Double chime (G4, C5)
      const notes = [392.00, 523.25];
      notes.forEach((f, idx) => {
        const delay = idx * 0.15;
        const osc = this.ctx!.createOscillator();
        const gain = this.ctx!.createGain();
        
        osc.type = "triangle";
        osc.frequency.setValueAtTime(f, t + delay);
        
        gain.gain.setValueAtTime(0, t);
        gain.gain.linearRampToValueAtTime(0.06, t + delay + 0.01);
        gain.gain.exponentialRampToValueAtTime(0.0001, t + delay + 0.8);
        
        osc.connect(gain);
        gain.connect(this.ctx!.destination);
        
        osc.start(t + delay);
        osc.stop(t + delay + 1.0);
      });
    } catch (e) {
      console.warn("Audio milestone play failed", e);
    }
  }
}

export const sarthiAudio = new AudioEngine();

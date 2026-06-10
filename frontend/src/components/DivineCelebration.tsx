import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface DivineCelebrationProps {
  onComplete?: () => void;
}

const ChakraSVG = () => (
  <svg viewBox="0 0 200 200" className="w-full h-full drop-shadow-[0_0_40px_rgba(251,191,36,0.9)]">
    <circle cx="100" cy="100" r="92" fill="none" stroke="#F59E0B" strokeWidth="6" strokeDasharray="15 10"/>
    <circle cx="100" cy="100" r="80" fill="none" stroke="#FBBF24" strokeWidth="3"/>
    <circle cx="100" cy="100" r="70" fill="none" stroke="#FCD34D" strokeWidth="1" strokeDasharray="4 4"/>
    <circle cx="100" cy="100" r="18" fill="#F59E0B" />
    <circle cx="100" cy="100" r="10" fill="#FEF3C7" />
    {[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330].map(angle => (
      <line key={angle} x1="100" y1="80" x2="100" y2="25" stroke="#FBBF24" strokeWidth="4" transform={`rotate(${angle} 100 100)`} />
    ))}
    {[15, 45, 75, 105, 135, 165, 195, 225, 255, 285, 315, 345].map(angle => (
      <polygon key={angle} points="96,10 104,10 100,-5" fill="#F59E0B" transform={`rotate(${angle} 100 100)`} />
    ))}
  </svg>
);

const MorpankhSVG = () => (
  <svg viewBox="0 0 100 150" className="w-full h-full" style={{ filter: 'drop-shadow(0px 0px 8px rgba(16, 185, 129, 0.6))' }}>
    <path d="M50,140 Q45,70 20,40 Q50,0 80,40 Q55,70 50,140" fill="none" stroke="#059669" strokeWidth="4" />
    <path d="M50,140 Q40,80 10,60" fill="none" stroke="#34D399" strokeWidth="1.5" />
    <path d="M50,140 Q60,80 90,60" fill="none" stroke="#34D399" strokeWidth="1.5" />
    <path d="M50,140 Q30,90 5,80" fill="none" stroke="#34D399" strokeWidth="1.5" />
    <path d="M50,140 Q70,90 95,80" fill="none" stroke="#34D399" strokeWidth="1.5" />
    <path d="M50,140 Q25,100 2,100" fill="none" stroke="#10B981" strokeWidth="1" />
    <path d="M50,140 Q75,100 98,100" fill="none" stroke="#10B981" strokeWidth="1" />
    {/* Eye */}
    <ellipse cx="50" cy="40" rx="16" ry="26" fill="#1E3A8A" />
    <ellipse cx="50" cy="40" rx="11" ry="19" fill="#10B981" />
    <ellipse cx="50" cy="40" rx="7" ry="12" fill="#F59E0B" />
    <circle cx="50" cy="35" r="3.5" fill="#1E1B4B" />
  </svg>
);

export const DivineCelebration: React.FC<DivineCelebrationProps> = ({ onComplete }) => {
  const [show, setShow] = useState(true);

  useEffect(() => {
    // Play a divine, magical chord using Web Audio API
    const playDivineSound = () => {
      try {
        const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
        if (!AudioContext) return;
        const ctx = new AudioContext();
        
        // A majestic, resonant chord (C Major with octaves)
        const frequencies = [261.63, 329.63, 392.00, 523.25]; 
        
        frequencies.forEach((freq, i) => {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          
          osc.type = "sine";
          osc.frequency.setValueAtTime(freq, ctx.currentTime);
          
          gain.gain.setValueAtTime(0, ctx.currentTime);
          gain.gain.linearRampToValueAtTime(0.3 - (i * 0.05), ctx.currentTime + 0.1);
          gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 4.5);
          
          osc.connect(gain);
          gain.connect(ctx.destination);
          
          osc.start();
          osc.stop(ctx.currentTime + 4.5);
        });

        // Magical sweep effect (Swarna particles sound)
        const sweep = ctx.createOscillator();
        const sweepGain = ctx.createGain();
        sweep.type = "triangle";
        sweep.frequency.setValueAtTime(600, ctx.currentTime);
        sweep.frequency.exponentialRampToValueAtTime(2400, ctx.currentTime + 2.0);
        
        sweepGain.gain.setValueAtTime(0, ctx.currentTime);
        sweepGain.gain.linearRampToValueAtTime(0.08, ctx.currentTime + 0.2);
        sweepGain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 2.5);
        
        sweep.connect(sweepGain);
        sweepGain.connect(ctx.destination);
        
        sweep.start();
        sweep.stop(ctx.currentTime + 2.5);
        
      } catch (e) {
        console.log("Audio playback failed", e);
      }
    };

    playDivineSound();

    // Show celebration for exactly 5 seconds, then unmount
    const timer = setTimeout(() => {
      setShow(false);
      if (onComplete) onComplete();
    }, 5500); // Give 5.5s for fade out animations to finish
    return () => clearTimeout(timer);
  }, [onComplete]);

  // Generate random particles
  const swarnaParticles = Array.from({ length: 80 }).map((_, i) => ({
    id: i,
    x: Math.random() * 100, // vw
    y: -20 - Math.random() * 20, // start above screen
    duration: 2 + Math.random() * 3, // fall duration
    delay: Math.random() * 1.5,
    size: 4 + Math.random() * 6,
  }));

  const morpankhParticles = Array.from({ length: 25 }).map((_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: -30 - Math.random() * 30,
    duration: 4 + Math.random() * 4,
    delay: Math.random() * 2,
    size: 30 + Math.random() * 30,
    rotation: Math.random() * 360,
    sway: 10 + Math.random() * 30, // px sway left/right
  }));

  return (
    <AnimatePresence>
      {show && (
        <div className="fixed inset-0 z-[100] pointer-events-none flex items-center justify-center overflow-hidden">
          
          {/* Background Dim & Flash */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: [0, 0.4, 0] }}
            transition={{ duration: 4, times: [0, 0.1, 1] }}
            className="absolute inset-0 bg-amber-900/30 mix-blend-overlay"
          />

          {/* Golden Ripple / Shockwave */}
          <motion.div
            initial={{ scale: 0, opacity: 1 }}
            animate={{ scale: [0, 4], opacity: [0.8, 0] }}
            transition={{ duration: 1.5, ease: "easeOut" }}
            className="absolute w-[400px] h-[400px] rounded-full border-[10px] border-amber-400 drop-shadow-[0_0_50px_rgba(251,191,36,1)]"
          />
          <motion.div
            initial={{ scale: 0, opacity: 1 }}
            animate={{ scale: [0, 6], opacity: [0.5, 0] }}
            transition={{ duration: 2, ease: "easeOut", delay: 0.2 }}
            className="absolute w-[300px] h-[300px] rounded-full bg-amber-500/20 blur-2xl"
          />

          {/* Central Chakra */}
          <motion.div
            initial={{ scale: 0, opacity: 0, rotate: -180 }}
            animate={{ 
              scale: [0, 1.2, 1], 
              opacity: [0, 1, 1, 0], 
              rotate: [-180, 720, 1080] 
            }}
            transition={{ 
              duration: 4.5, 
              times: [0, 0.1, 0.8, 1],
              ease: "circOut"
            }}
            className="absolute w-64 h-64 md:w-96 md:h-96 z-10"
          >
            <ChakraSVG />
          </motion.div>

          {/* Vijay Bhava Banner */}
          <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.8 }}
            animate={{ opacity: [0, 1, 1, 0], y: [50, 0, 0, -50], scale: [0.8, 1.1, 1, 0.9] }}
            transition={{ duration: 4, times: [0, 0.1, 0.8, 1] }}
            className="absolute z-20 flex flex-col items-center justify-center drop-shadow-[0_0_20px_rgba(251,191,36,0.8)]"
          >
            <h1 className="text-5xl md:text-7xl font-black text-transparent bg-clip-text bg-gradient-to-b from-amber-200 via-amber-400 to-amber-600 uppercase tracking-widest font-display" style={{ WebkitTextStroke: '1px rgba(120,53,15,0.5)' }}>
              Vijay Bhava
            </h1>
            <p className="text-amber-100 text-lg md:text-xl font-bold tracking-[0.2em] mt-2 uppercase shadow-amber-900/50">
              Project Manifested
            </p>
          </motion.div>

          {/* Swarna Varsha (Golden Shower) */}
          {swarnaParticles.map(p => (
            <motion.div
              key={`swarna-${p.id}`}
              initial={{ x: `${p.x}vw`, y: `${p.y}vh`, opacity: 0 }}
              animate={{ 
                y: [`${p.y}vh`, '110vh'],
                opacity: [0, 1, 1, 0]
              }}
              transition={{
                duration: p.duration,
                delay: p.delay,
                ease: "linear"
              }}
              className="absolute rounded-full bg-amber-400 drop-shadow-[0_0_5px_rgba(251,191,36,1)]"
              style={{ width: p.size, height: p.size }}
            />
          ))}

          {/* Morpankh Fall */}
          {morpankhParticles.map(p => (
            <motion.div
              key={`morpankh-${p.id}`}
              initial={{ x: `${p.x}vw`, y: `${p.y}vh`, rotate: p.rotation, opacity: 0 }}
              animate={{ 
                x: [`${p.x}vw`, `${p.x + (p.sway/10)}vw`, `${p.x - (p.sway/10)}vw`, `${p.x}vw`],
                y: [`${p.y}vh`, '110vh'],
                rotate: [p.rotation, p.rotation + 45, p.rotation - 45, p.rotation + 90],
                opacity: [0, 1, 1, 0]
              }}
              transition={{
                duration: p.duration,
                delay: p.delay,
                ease: "linear",
                x: { repeat: Infinity, duration: 1.5, repeatType: "mirror", ease: "easeInOut" }
              }}
              className="absolute"
              style={{ width: p.size, height: p.size * 1.5 }}
            >
              <MorpankhSVG />
            </motion.div>
          ))}

        </div>
      )}
    </AnimatePresence>
  );
};

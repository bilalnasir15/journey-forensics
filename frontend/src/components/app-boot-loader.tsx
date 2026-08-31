"use client";

import {
  Activity,
  Fingerprint,
  Layers3,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import {
  AnimatePresence,
  motion,
} from "motion/react";

import {
  useEffect,
  useState,
} from "react";


// ============================================================
// APP BOOT LOADER
// ============================================================

export default function AppBootLoader() {

  const [
    visible,
    setVisible,
  ] = useState(true);


  const [
    progress,
    setProgress,
  ] = useState(0);


  const [
    stage,
    setStage,
  ] = useState(
    "Initializing forensic engine"
  );


  useEffect(() => {

    let frame: number;

    let start =
      performance.now();


    const duration =
      1400;


    function animate(
      currentTime: number
    ) {

      const elapsed =
        currentTime - start;


      const percentage =
        Math.min(
          100,
          Math.round(
            (
              elapsed /
              duration
            ) * 100
          )
        );


      setProgress(
        percentage
      );


      if (
        percentage <
        30
      ) {

        setStage(
          "Initializing forensic engine"
        );

      } else if (
        percentage <
        60
      ) {

        setStage(
          "Loading analytical layers"
        );

      } else if (
        percentage <
        85
      ) {

        setStage(
          "Synchronizing intelligence"
        );

      } else {

        setStage(
          "Forensic engine ready"
        );

      }


      if (
        percentage <
        100
      ) {

        frame =
          requestAnimationFrame(
            animate
          );

      } else {

        window.setTimeout(
          () => {

            setVisible(
              false
            );

          },
          280
        );

      }

    }


    frame =
      requestAnimationFrame(
        animate
      );


    return () => {

      cancelAnimationFrame(
        frame
      );

    };

  }, []);


  return (
    <AnimatePresence>
      {visible && (

        <motion.div
          initial={{
            opacity: 1,
          }}
          exit={{
            opacity: 0,
          }}
          transition={{
            duration: 0.65,
            ease: "easeInOut",
          }}
          className="fixed inset-0 z-[9999] flex items-center justify-center overflow-hidden bg-[#050d18]"
        >

          {/* ==================================================
              AMBIENT LIGHT
              ================================================== */}

          <motion.div
            animate={{
              scale: [
                1,
                1.18,
                1,
              ],
              opacity: [
                0.18,
                0.3,
                0.18,
              ],
            }}
            transition={{
              duration: 3.2,
              repeat: Infinity,
              ease: "easeInOut",
            }}
            className="pointer-events-none absolute left-1/2 top-1/2 h-[30rem] w-[30rem] -translate-x-1/2 -translate-y-1/2 rounded-full bg-cyan-400/10 blur-3xl"
          />


          <motion.div
            animate={{
              x: [
                -40,
                40,
                -40,
              ],
              opacity: [
                0.08,
                0.16,
                0.08,
              ],
            }}
            transition={{
              duration: 5,
              repeat: Infinity,
              ease: "easeInOut",
            }}
            className="pointer-events-none absolute right-[-8rem] top-1/4 h-80 w-80 rounded-full bg-violet-500/10 blur-3xl"
          />


          {/* ==================================================
              SCAN GRID
              ================================================== */}

          <div className="pointer-events-none absolute inset-0 opacity-[0.035] [background-image:linear-gradient(rgba(255,255,255,.7)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.7)_1px,transparent_1px)] [background-size:42px_42px]" />


          {/* ==================================================
              CENTER
              ================================================== */}

          <div className="relative flex w-[min(90vw,440px)] flex-col items-center text-center">


            {/* =================================================
                LOGO
                ================================================= */}

            <div className="relative">

              <motion.div
                animate={{
                  rotate: 360,
                }}
                transition={{
                  duration: 10,
                  repeat: Infinity,
                  ease: "linear",
                }}
                className="absolute -inset-5 rounded-[2rem] border border-cyan-300/10 border-dashed"
              />


              <motion.div
                animate={{
                  boxShadow: [
                    "0 0 0 rgba(103,232,249,0)",
                    "0 0 45px rgba(103,232,249,.16)",
                    "0 0 0 rgba(103,232,249,0)",
                  ],
                }}
                transition={{
                  duration: 2.3,
                  repeat: Infinity,
                }}
                className="relative flex h-20 w-20 items-center justify-center rounded-[1.7rem] border border-cyan-300/20 bg-cyan-300/10"
              >

                <Layers3 className="h-9 w-9 text-cyan-300" />

              </motion.div>


              <motion.div
                initial={{
                  scale: 0,
                  opacity: 0,
                }}
                animate={{
                  scale: 1,
                  opacity: 1,
                }}
                transition={{
                  delay: 0.2,
                  duration: 0.5,
                  type: "spring",
                }}
                className="absolute -bottom-2 -right-2 flex h-7 w-7 items-center justify-center rounded-xl border border-emerald-300/20 bg-[#07111f] text-emerald-300"
              >

                <ShieldCheck className="h-3.5 w-3.5" />

              </motion.div>

            </div>


            {/* =================================================
                BRAND
                ================================================= */}

            <motion.div
              initial={{
                opacity: 0,
                y: 12,
              }}
              animate={{
                opacity: 1,
                y: 0,
              }}
              transition={{
                delay: 0.15,
              }}
              className="mt-8"
            >

              <p className="text-base font-semibold tracking-[0.34em] text-white">
                JOURNEY
              </p>

              <p className="mt-1 text-[10px] tracking-[0.48em] text-cyan-300/70">
                FORENSICS
              </p>

            </motion.div>


            {/* =================================================
                STATUS
                ================================================= */}

            <motion.div
              initial={{
                opacity: 0,
              }}
              animate={{
                opacity: 1,
              }}
              transition={{
                delay: 0.35,
              }}
              className="mt-10 flex items-center gap-2 text-xs text-white/45"
            >

              <motion.span
                animate={{
                  scale: [
                    1,
                    1.35,
                    1,
                  ],
                  opacity: [
                    0.5,
                    1,
                    0.5,
                  ],
                }}
                transition={{
                  duration: 1.2,
                  repeat: Infinity,
                }}
                className="h-2 w-2 rounded-full bg-cyan-300"
              />

              {stage}

            </motion.div>


            {/* =================================================
                PROGRESS
                ================================================= */}

            <div className="mt-5 w-full">

              <div className="h-[3px] overflow-hidden rounded-full bg-white/5">

                <motion.div
                  initial={{
                    width: 0,
                  }}
                  animate={{
                    width: `${progress}%`,
                  }}
                  transition={{
                    duration: 0.1,
                    ease: "linear",
                  }}
                  className="relative h-full rounded-full bg-gradient-to-r from-cyan-300 via-blue-400 to-violet-400"
                >

                  <motion.div
                    animate={{
                      x: [
                        "-20%",
                        "120%",
                      ],
                    }}
                    transition={{
                      duration: 1.15,
                      repeat: Infinity,
                      ease: "linear",
                    }}
                    className="absolute inset-y-0 w-20 bg-white/50 blur-sm"
                  />

                </motion.div>

              </div>


              <div className="mt-2 flex justify-between text-[9px] uppercase tracking-[0.16em] text-white/20">

                <span>
                  Secure startup
                </span>

                <span>
                  {progress}%
                </span>

              </div>

            </div>


            {/* =================================================
                SIGNALS
                ================================================= */}

            <div className="mt-8 grid w-full grid-cols-3 gap-2">

              {[
                {
                  icon: Activity,
                  label: "Signals",
                },
                {
                  icon: Fingerprint,
                  label: "Identity",
                },
                {
                  icon: Sparkles,
                  label: "Analysis",
                },
              ].map(
                (
                  item,
                  index
                ) => {

                  const Icon =
                    item.icon;

                  return (

                    <motion.div
                      key={
                        item.label
                      }
                      initial={{
                        opacity: 0,
                        y: 8,
                      }}
                      animate={{
                        opacity: 1,
                        y: 0,
                      }}
                      transition={{
                        delay:
                          0.45 +
                          index *
                            0.08,
                      }}
                      className="rounded-2xl border border-white/5 bg-white/[0.025] px-3 py-3"
                    >

                      <Icon className="mx-auto h-4 w-4 text-cyan-300/60" />

                      <p className="mt-2 text-[9px] uppercase tracking-[0.12em] text-white/20">
                        {item.label}
                      </p>

                    </motion.div>

                  );

                }
              )}

            </div>

          </div>

        </motion.div>

      )}
    </AnimatePresence>
  );
}
"use client";

import {
  ArrowLeft,
  CheckCircle2,
  CloudUpload,
  FileSpreadsheet,
  FileText,
  Loader2,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  X,
  XCircle,
} from "lucide-react";

import { motion } from "motion/react";

import Link from "next/link";

import {
  DragEvent,
  ChangeEvent,
  useRef,
  useState,
} from "react";

import {
  uploadCSV,
  type UploadResponse,
} from "@/lib/api";


// ============================================================
// CONSTANTS
// ============================================================

const MAX_FILE_SIZE =
  10 * 1024 * 1024;

const MAX_FILE_SIZE_LABEL =
  "10 MB";


// ============================================================
// PAGE
// ============================================================

export default function UploadPage() {

  // ==========================================================
  // STATE
  // ==========================================================

  const fileInputRef =
    useRef<HTMLInputElement | null>(
      null
    );


  const [selectedFile, setSelectedFile] =
    useState<File | null>(
      null
    );


  const [isDragging, setIsDragging] =
    useState(false);


  const [uploading, setUploading] =
    useState(false);


  const [uploadProgress, setUploadProgress] =
    useState(0);


  const [result, setResult] =
    useState<UploadResponse | null>(
      null
    );


  const [error, setError] =
    useState<string | null>(
      null
    );


  // ==========================================================
  // FILE VALIDATION
  // ==========================================================

  function validateFile(
    file: File
  ): string | null {

    if (!file) {

      return "Please select a CSV file.";

    }


    const fileName =
      file.name.toLowerCase();


    if (!fileName.endsWith(".csv")) {

      return "Only CSV files are supported.";

    }


    if (file.size === 0) {

      return "The selected file is empty.";

    }


    if (file.size > MAX_FILE_SIZE) {

      return `File is too large. Maximum size is ${MAX_FILE_SIZE_LABEL}.`;

    }


    return null;
  }


  // ==========================================================
  // SELECT FILE
  // ==========================================================

  function handleFileSelect(
    file: File
  ) {

    setResult(null);
    setError(null);
    setUploadProgress(0);


    const validationError =
      validateFile(file);


    if (validationError) {

      setSelectedFile(null);
      setError(
        validationError
      );

      return;
    }


    setSelectedFile(file);
  }


  // ==========================================================
  // INPUT CHANGE
  // ==========================================================

  function handleInputChange(
    event: ChangeEvent<HTMLInputElement>
  ) {

    const file =
      event.target.files?.[0];


    if (!file) {
      return;
    }


    handleFileSelect(file);
  }


  // ==========================================================
  // DRAG EVENTS
  // ==========================================================

  function handleDragOver(
    event: DragEvent<HTMLDivElement>
  ) {

    event.preventDefault();

    setIsDragging(true);
  }


  function handleDragLeave(
    event: DragEvent<HTMLDivElement>
  ) {

    event.preventDefault();

    setIsDragging(false);
  }


  function handleDrop(
    event: DragEvent<HTMLDivElement>
  ) {

    event.preventDefault();

    setIsDragging(false);


    const file =
      event.dataTransfer.files?.[0];


    if (!file) {
      return;
    }


    handleFileSelect(file);
  }


  // ==========================================================
  // OPEN FILE PICKER
  // ==========================================================

  function openFilePicker() {

    fileInputRef.current?.click();

  }


  // ==========================================================
  // CLEAR
  // ==========================================================

  function clearSelection() {

    setSelectedFile(null);
    setResult(null);
    setError(null);
    setUploadProgress(0);


    if (fileInputRef.current) {

      fileInputRef.current.value = "";

    }
  }


  // ==========================================================
  // UPLOAD
  // ==========================================================

  async function handleUpload() {

    if (!selectedFile) {

      setError(
        "Please select a CSV file first."
      );

      return;
    }


    const validationError =
      validateFile(
        selectedFile
      );


    if (validationError) {

      setError(
        validationError
      );

      return;
    }


    try {

      setUploading(true);

      setError(null);

      setResult(null);


      // Visual upload progress.
      // The backend API does not currently expose
      // streaming byte-level progress.

      setUploadProgress(15);


      const progressTimer =
        window.setInterval(() => {

          setUploadProgress(
            (current) => {

              if (current >= 85) {

                return current;

              }

              return current + 10;

            }
          );

        }, 180);


      const data =
        await uploadCSV(
          selectedFile
        );


      window.clearInterval(
        progressTimer
      );


      setUploadProgress(100);

      setResult(
        data
      );


    } catch (err) {

      setUploadProgress(0);

      setError(
        err instanceof Error
          ? err.message
          : "Upload failed."
      );

    } finally {

      setUploading(false);

    }
  }


  // ==========================================================
  // FORMAT FILE SIZE
  // ==========================================================

  function formatFileSize(
    bytes: number
  ): string {

    if (bytes < 1024) {

      return `${bytes} B`;

    }


    if (bytes < 1024 * 1024) {

      return `${(
        bytes / 1024
      ).toFixed(1)} KB`;

    }


    return `${(
      bytes /
      (1024 * 1024)
    ).toFixed(2)} MB`;
  }


  return (

    <main className="min-h-screen bg-[#07111f] text-white">


      {/* ======================================================
          AMBIENT BACKGROUND
          ====================================================== */}

      <div className="pointer-events-none fixed inset-0 overflow-hidden">

        <motion.div
          className="absolute -left-40 top-10 h-[28rem] w-[28rem] rounded-full bg-cyan-400/10 blur-3xl"
          animate={{
            x: [0, 60, 0],
            y: [0, 30, 0],
            scale: [1, 1.08, 1],
          }}
          transition={{
            duration: 11,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />


        <motion.div
          className="absolute right-[-150px] top-1/4 h-[32rem] w-[32rem] rounded-full bg-violet-500/10 blur-3xl"
          animate={{
            x: [0, -50, 0],
            y: [0, 50, 0],
            scale: [1, 1.1, 1],
          }}
          transition={{
            duration: 14,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />


        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(59,130,246,0.08),transparent_42%)]" />

      </div>


      {/* ======================================================
          NAVIGATION
          ====================================================== */}

      <nav className="relative z-10 border-b border-white/10 bg-[#07111f]/75 backdrop-blur-xl">

        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">


          <Link
            href="/"
            className="flex items-center gap-3"
          >

            <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-cyan-300/20 bg-cyan-300/10">

              <UploadCloud className="h-5 w-5 text-cyan-300" />

            </div>


            <div>

              <p className="text-sm font-semibold tracking-[0.22em]">
                JOURNEY
              </p>

              <p className="text-xs tracking-[0.3em] text-cyan-300/70">
                FORENSICS
              </p>

            </div>

          </Link>


          <div className="flex items-center gap-2 rounded-full border border-cyan-300/10 bg-cyan-300/5 px-4 py-2 text-xs text-cyan-200/75">

            <Sparkles className="h-3.5 w-3.5" />

            Data ingestion

          </div>

        </div>

      </nav>


      {/* ======================================================
          CONTENT
          ====================================================== */}

      <section className="relative z-10 mx-auto max-w-5xl px-6 py-12">


        {/* ====================================================
            HEADER
            ==================================================== */}

        <motion.div
          initial={{
            opacity: 0,
            y: 20,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
        >

          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm text-white/40 transition hover:text-white"
          >

            <ArrowLeft className="h-4 w-4" />

            Back to overview

          </Link>


          <div className="mt-8">

            <div className="flex items-center gap-2 text-sm text-cyan-300/70">

              <FileSpreadsheet className="h-4 w-4" />

              Data upload

            </div>


            <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">

              Bring your data
              <span className="block bg-gradient-to-r from-cyan-300 via-blue-400 to-violet-400 bg-clip-text text-transparent">
                into the investigation.
              </span>

            </h1>


            <p className="mt-4 max-w-2xl text-base leading-7 text-white/45">

              Upload a CSV dataset and let Journey
              Forensics validate, inspect and store it
              for analysis.

            </p>

          </div>

        </motion.div>


        {/* ====================================================
            UPLOAD CARD
            ==================================================== */}

        <motion.div
          initial={{
            opacity: 0,
            y: 25,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          transition={{
            delay: 0.12,
          }}
          className="mt-10 rounded-[2rem] border border-white/10 bg-white/[0.035] p-5 backdrop-blur-xl sm:p-7"
        >

          {/* DROP ZONE */}

          {!selectedFile && !result && (

            <motion.div
              onDragOver={
                handleDragOver
              }
              onDragLeave={
                handleDragLeave
              }
              onDrop={
                handleDrop
              }
              animate={{
                scale:
                  isDragging
                    ? 1.01
                    : 1,
              }}
              className={`relative flex min-h-[360px] flex-col items-center justify-center rounded-[1.6rem] border border-dashed p-8 text-center transition ${
                isDragging
                  ? "border-cyan-300/60 bg-cyan-300/[0.08]"
                  : "border-white/10 bg-black/10 hover:border-cyan-300/25 hover:bg-cyan-300/[0.025]"
              }`}
            >

              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,text/csv"
                onChange={
                  handleInputChange
                }
                className="hidden"
              />


              <motion.div
                animate={{
                  y:
                    isDragging
                      ? -7
                      : [0, -4, 0],
                }}
                transition={
                  isDragging
                    ? {
                        duration: 0.2,
                      }
                    : {
                        duration: 3,
                        repeat: Infinity,
                        ease: "easeInOut",
                      }
                }
                className="flex h-20 w-20 items-center justify-center rounded-3xl border border-cyan-300/20 bg-cyan-300/10"
              >

                <CloudUpload className="h-9 w-9 text-cyan-300" />

              </motion.div>


              <h2 className="mt-7 text-xl font-semibold">
                Drop your CSV here
              </h2>


              <p className="mt-2 text-sm text-white/35">
                or choose a file from your computer
              </p>


              <motion.button
                type="button"
                onClick={
                  openFilePicker
                }
                whileHover={{
                  scale: 1.03,
                }}
                whileTap={{
                  scale: 0.98,
                }}
                className="mt-7 rounded-2xl bg-cyan-300 px-6 py-3 text-sm font-medium text-[#07111f]"
              >
                Choose CSV file
              </motion.button>


              <div className="mt-6 flex flex-wrap justify-center gap-3 text-[11px] text-white/25">

                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">
                  CSV only
                </span>

                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">
                  Max 10 MB
                </span>

                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">
                  Secure server storage
                </span>

              </div>

            </motion.div>

          )}


          {/* ==================================================
              FILE SELECTED
              ================================================== */}

          {selectedFile && !result && (

            <motion.div
              initial={{
                opacity: 0,
                scale: 0.98,
              }}
              animate={{
                opacity: 1,
                scale: 1,
              }}
              className="rounded-[1.6rem] border border-cyan-300/15 bg-cyan-300/[0.035] p-6"
            >

              <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">


                <div className="flex items-center gap-4">

                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-300/10">

                    <FileText className="h-6 w-6 text-cyan-300" />

                  </div>


                  <div className="min-w-0">

                    <p className="truncate font-medium">
                      {selectedFile.name}
                    </p>

                    <p className="mt-1 text-xs text-white/35">

                      {formatFileSize(
                        selectedFile.size
                      )}

                    </p>

                  </div>

                </div>


                {!uploading && (

                  <button
                    onClick={
                      clearSelection
                    }
                    className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-white/40 transition hover:bg-white/10 hover:text-white"
                  >

                    <X className="h-4 w-4" />

                  </button>

                )}

              </div>


              {/* VALIDATION */}

              <div className="mt-6 grid gap-3 sm:grid-cols-3">

                <div className="rounded-2xl border border-white/5 bg-black/10 p-4">

                  <p className="text-[10px] text-white/30">
                    Format
                  </p>

                  <p className="mt-1 text-sm text-emerald-200">
                    CSV validated
                  </p>

                </div>


                <div className="rounded-2xl border border-white/5 bg-black/10 p-4">

                  <p className="text-[10px] text-white/30">
                    File size
                  </p>

                  <p className="mt-1 text-sm">
                    {formatFileSize(
                      selectedFile.size
                    )}
                  </p>

                </div>


                <div className="rounded-2xl border border-white/5 bg-black/10 p-4">

                  <p className="text-[10px] text-white/30">
                    Destination
                  </p>

                  <p className="mt-1 text-sm text-white/65">
                    Analytics storage
                  </p>

                </div>

              </div>


              {/* PROGRESS */}

              {uploading && (

                <div className="mt-7">

                  <div className="mb-2 flex items-center justify-between text-xs">

                    <span className="text-white/40">
                      Uploading dataset
                    </span>

                    <span className="text-cyan-200">
                      {uploadProgress}%
                    </span>

                  </div>


                  <div className="h-2 overflow-hidden rounded-full bg-white/5">

                    <motion.div
                      className="h-full rounded-full bg-gradient-to-r from-cyan-300 via-blue-400 to-violet-400"
                      initial={{
                        width: "0%",
                      }}
                      animate={{
                        width:
                          `${uploadProgress}%`,
                      }}
                    />

                  </div>

                </div>

              )}


              {!uploading && (

                <motion.button
                  type="button"
                  onClick={
                    handleUpload
                  }
                  whileHover={{
                    scale: 1.01,
                    boxShadow:
                      "0 12px 40px rgba(103,232,249,0.12)",
                  }}
                  whileTap={{
                    scale: 0.99,
                  }}
                  className="mt-7 flex w-full items-center justify-center gap-2 rounded-2xl bg-cyan-300 px-6 py-3.5 text-sm font-medium text-[#07111f]"
                >

                  <CloudUpload className="h-4 w-4" />

                  Upload dataset

                </motion.button>

              )}

              {uploading && (

                <div className="mt-7 flex items-center justify-center gap-2 text-sm text-cyan-200/70">

                  <Loader2 className="h-4 w-4 animate-spin" />

                  Processing your dataset...

                </div>

              )}

            </motion.div>

          )}


          {/* ==================================================
              SUCCESS
              ================================================== */}

          {result && (

            <motion.div
              initial={{
                opacity: 0,
                y: 15,
              }}
              animate={{
                opacity: 1,
                y: 0,
              }}
              className="rounded-[1.6rem] border border-emerald-300/15 bg-emerald-300/[0.035] p-7"
            >

              <div className="flex flex-col items-center text-center">

                <motion.div
                  initial={{
                    scale: 0,
                  }}
                  animate={{
                    scale: 1,
                  }}
                  transition={{
                    type: "spring",
                    stiffness: 220,
                    damping: 14,
                  }}
                  className="flex h-16 w-16 items-center justify-center rounded-3xl border border-emerald-300/20 bg-emerald-300/10"
                >

                  <CheckCircle2 className="h-8 w-8 text-emerald-300" />

                </motion.div>


                <h2 className="mt-5 text-2xl font-semibold">
                  Dataset uploaded successfully
                </h2>


                <p className="mt-2 text-sm text-white/35">
                  Journey Forensics accepted the dataset
                  and stored it safely.
                </p>

              </div>


              {/* RESULT METRICS */}

              <div className="mt-8 grid gap-3 sm:grid-cols-3">

                <div className="rounded-2xl border border-white/5 bg-black/10 p-5">

                  <p className="text-[10px] text-white/30">
                    Original filename
                  </p>

                  <p className="mt-2 truncate text-sm font-medium">
                    {result.filename}
                  </p>

                </div>


                <div className="rounded-2xl border border-white/5 bg-black/10 p-5">

                  <p className="text-[10px] text-white/30">
                    Rows
                  </p>

                  <p className="mt-2 text-2xl font-semibold">
                    {result.rows.toLocaleString()}
                  </p>

                </div>


                <div className="rounded-2xl border border-white/5 bg-black/10 p-5">

                  <p className="text-[10px] text-white/30">
                    Columns
                  </p>

                  <p className="mt-2 text-2xl font-semibold">
                    {result.columns.toLocaleString()}
                  </p>

                </div>

              </div>


              {/* STORED FILE */}

              <div className="mt-4 rounded-2xl border border-emerald-300/10 bg-emerald-300/[0.025] p-5">

                <div className="flex items-center gap-2 text-sm text-emerald-200/80">

                  <ShieldCheck className="h-4 w-4" />

                  Stored successfully

                </div>


                <p className="mt-3 break-all font-mono text-xs text-white/40">
                  {result.stored_filename}
                </p>


                <p className="mt-2 text-xs text-white/30">
                  Status: {result.status}
                </p>

              </div>


              {/* NEW UPLOAD */}

              <motion.button
                type="button"
                onClick={
                  clearSelection
                }
                whileHover={{
                  scale: 1.01,
                }}
                whileTap={{
                  scale: 0.99,
                }}
                className="mt-7 flex w-full items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-6 py-3.5 text-sm text-white/65 transition hover:bg-white/10 hover:text-white"
              >

                <RefreshCw className="h-4 w-4" />

                Upload another dataset

              </motion.button>

            </motion.div>

          )}


          {/* ==================================================
              ERROR
              ================================================== */}

          {error && (

            <motion.div
              initial={{
                opacity: 0,
                y: 10,
              }}
              animate={{
                opacity: 1,
                y: 0,
              }}
              className="mt-5 flex items-start gap-3 rounded-2xl border border-red-300/15 bg-red-300/[0.04] p-5"
            >

              <XCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-300" />


              <div className="flex-1">

                <p className="text-sm font-medium text-red-200">
                  Upload could not be completed
                </p>


                <p className="mt-1 text-sm leading-6 text-white/40">
                  {error}
                </p>

              </div>

            </motion.div>

          )}

        </motion.div>


        {/* ====================================================
            TRUST / INFO
            ==================================================== */}

        <div className="mt-5 grid gap-4 md:grid-cols-3">

          {[
            {
              icon: ShieldCheck,
              title: "Validated ingestion",
              text: "CSV format and upload constraints are checked before submission.",
            },

            {
              icon: FileSpreadsheet,
              title: "Dataset metadata",
              text: "Rows and columns are returned immediately after successful ingestion.",
            },

            {
              icon: Sparkles,
              title: "Ready for analysis",
              text: "Uploaded files can become part of the broader investigation workflow.",
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
                  key={item.title}
                  initial={{
                    opacity: 0,
                    y: 15,
                  }}
                  animate={{
                    opacity: 1,
                    y: 0,
                  }}
                  transition={{
                    delay:
                      0.25 +
                      index *
                        0.08,
                  }}
                  className="rounded-3xl border border-white/10 bg-white/[0.03] p-5"
                >

                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/5">

                    <Icon className="h-5 w-5 text-cyan-300" />

                  </div>


                  <h3 className="mt-5 text-sm font-semibold">
                    {item.title}
                  </h3>


                  <p className="mt-2 text-xs leading-6 text-white/35">
                    {item.text}
                  </p>

                </motion.div>

              );

            }
          )}

        </div>


      </section>


      {/* ======================================================
          FOOTER
          ====================================================== */}

      <footer className="relative z-10 border-t border-white/10 px-6 py-6">

        <div className="mx-auto flex max-w-5xl justify-between text-xs text-white/25">

          <span>
            Journey Forensics
          </span>

          <span>
            Secure data ingestion
          </span>

        </div>

      </footer>

    </main>
  );
}
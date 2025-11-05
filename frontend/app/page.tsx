"use client";

// Location: frontend/app/page.tsx
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import {
    ArrowRight,
    Sparkles,
    Atom,
    FlaskConical,
    Layers,
    Satellite,
} from "lucide-react";

const heroVideo = "https://cdn.coverr.co/videos/coverr-lab-analyst-looking-into-a-microscope-0148/1080p.mp4";
const gallery = [
    {
        src: "https://images-assets.nasa.gov/image/PIA24420/PIA24420~orig.jpg",
        alt: "James Webb telescope imagery of distant galaxies",
    },
    {
        src: "https://images.unsplash.com/photo-1526378722484-bd91ca387e72?auto=format&fit=crop&w=1200&q=80",
        alt: "Scientist working with holographic data",
    },
    {
        src: "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
        alt: "Robotic arm operating in a research facility",
    },
];

const features = [
    {
        icon: Sparkles,
        title: "Idea Genesis",
        description:
            "Fuse foundation models with your domain knowledge to uncover novel experiment hypotheses in minutes.",
    },
    {
        icon: Atom,
        title: "Automated Experimentation",
        description:
            "Spin up reproducible experiment pipelines that compile, train, and benchmark your concepts automatically.",
    },
    {
        icon: FlaskConical,
        title: "Living Literature Review",
        description:
            "Curate a dynamic evidence graph that stays synchronized with the latest arXiv and journal releases.",
    },
    {
        icon: Layers,
        title: "Multimodal Insights",
        description:
            "Blend structured metrics, simulation outputs, and qualitative observations inside one command center.",
    },
];

export default function IntroPage() {
    return (
        <div className="relative min-h-screen overflow-hidden bg-slate-950 text-white">
            <div className="pointer-events-none absolute inset-0">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.25),_transparent_55%)]" />
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom,_rgba(168,85,247,0.25),_transparent_60%)]" />
                <div className="absolute -top-32 left-24 h-72 w-72 rounded-full bg-blue-500/20 blur-3xl" />
                <div className="absolute bottom-0 right-0 h-96 w-96 rounded-full bg-emerald-500/10 blur-3xl" />
                <div className="absolute -bottom-40 left-1/2 h-80 w-80 -translate-x-1/2 rounded-full bg-sky-500/10 blur-3xl" />
            </div>

            <div className="relative z-10">
                <header className="flex items-center justify-between px-6 py-4 md:px-12">
                    <div className="flex items-center gap-3 text-lg font-semibold tracking-tight">
                        <Satellite className="h-6 w-6 text-sky-400" />
                        SciFusion Research Suite
                    </div>
                    <div className="hidden space-x-4 text-sm font-medium md:flex">
                        <Link href="/login" className="text-white/70 hover:text-white">
                            Platform
                        </Link>
                        <Link href="https://github.com/kmitofficial/SciFusion-G490-PS25" className="text-white/70 hover:text-white" target="_blank" rel="noreferrer">
                            GitHub
                        </Link>
                        <Link href="#features" className="text-white/70 hover:text-white">
                            Capabilities
                        </Link>
                    </div>
                    <Button asChild size="lg" className="bg-gradient-to-r from-sky-500 via-indigo-500 to-purple-500 shadow-lg shadow-indigo-500/30 text-white">
                        <Link href="/login">Sign In</Link>
                    </Button>
                </header>

                <main className="mx-auto flex max-w-7xl flex-col gap-24 px-6 pb-24 pt-12 md:px-12">
                    <section className="grid grid-cols-1 items-center gap-16 md:grid-cols-2">
                        <motion.div
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.6 }}
                            className="space-y-8"
                        >
                            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1 text-sm text-white/70">
                                <Sparkles className="h-4 w-4 text-sky-300" />
                                Accelerate hypothesis to reproducible result
                            </div>
                            <h1 className="text-4xl font-bold tracking-tight md:text-6xl">
                                The mission control for <span className="bg-gradient-to-r from-sky-400 via-indigo-400 to-fuchsia-500 bg-clip-text text-transparent">scientific imagination</span>
                            </h1>
                            <p className="text-lg text-white/70 md:text-xl">
                                SciFusion orchestrates literature intelligence, code generation, and experimental automation into a single AI-first lab console. Explore galaxies of research faster than ever before.
                            </p>
                            <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
                                <Button asChild size="lg" className="bg-gradient-to-r from-sky-500 via-indigo-500 to-purple-500 shadow-lg shadow-indigo-500/30">
                                    <Link href="/signup" className="flex items-center gap-2">
                                        Get Started
                                        <ArrowRight className="h-5 w-5" />
                                    </Link>
                                </Button>
                                <Button asChild size="lg" variant="outline" className="border-white/20 bg-white/10 text-white hover:bg-white/20">
                                    <Link href="#features">Discover the platform</Link>
                                </Button>
                            </div>
                            <div className="flex flex-col gap-4 text-sm text-white/60 sm:flex-row sm:items-center sm:gap-8">
                                <div>
                                    <p className="font-semibold text-white">92% faster</p>
                                    <p>from problem statement to validated baseline.</p>
                                </div>
                                <div>
                                    <p className="font-semibold text-white">Auto-generated</p>
                                    <p>experiment notebooks, datasets, and logs.</p>
                                </div>
                            </div>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ duration: 0.7 }}
                            className="relative w-full"
                        >
                            <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-white/5 shadow-2xl backdrop-blur">
                                <video
                                    src={heroVideo}
                                    autoPlay
                                    loop
                                    muted
                                    playsInline
                                    className="h-full w-full object-cover"
                                />
                                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/60 via-transparent to-slate-900/40" />
                                <div className="absolute bottom-6 left-6 right-6 rounded-2xl border border-white/10 bg-slate-950/60 p-4 shadow-xl backdrop-blur">
                                    <p className="text-xs uppercase tracking-[0.2em] text-sky-300">
                                        Live pipeline playback
                                    </p>
                                    <p className="mt-2 text-sm text-white/80">
                                        Monitor retrieval, ideation, and experimentation streams in real time. Every run stays fully annotated and reproducible.
                                    </p>
                                </div>
                            </div>
                        </motion.div>
                    </section>

                    <section id="features" className="space-y-12">
                        <div className="flex flex-col items-start gap-4 md:flex-row md:items-end md:justify-between">
                            <div>
                                <p className="text-sm uppercase tracking-[0.4em] text-sky-300">Core Systems</p>
                                <h2 className="mt-2 text-3xl font-semibold md:text-4xl">Everything you need to command a research program</h2>
                            </div>
                            <p className="max-w-xl text-base text-white/70">
                                SciFusion threads together retrieval-augmented generation, execution planning, and experiment telemetry so you can iterate with scientific rigor and creative velocity.
                            </p>
                        </div>
                        <div className="grid gap-6 md:grid-cols-2">
                            {features.map(({ icon: Icon, title, description }) => (
                                <div
                                    key={title}
                                    className="group relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-6 shadow-lg transition hover:border-sky-400/40 hover:shadow-sky-500/20"
                                >
                                    <div className="absolute -top-20 right-0 h-40 w-40 rounded-full bg-sky-500/10 blur-3xl transition group-hover:bg-sky-400/20" />
                                    <Icon className="h-10 w-10 text-sky-300" />
                                    <h3 className="mt-4 text-xl font-semibold text-white">{title}</h3>
                                    <p className="mt-2 text-sm text-white/70">{description}</p>
                                </div>
                            ))}
                        </div>
                    </section>

                    <section className="grid gap-10 lg:grid-cols-[1.2fr_1fr]">
                        <div className="space-y-6 rounded-3xl border border-white/10 bg-white/5 p-8 shadow-xl">
                            <p className="text-sm uppercase tracking-[0.35em] text-sky-300">Immersive visuals</p>
                            <h2 className="text-3xl font-semibold">Research that feels like deep space exploration</h2>
                            <p className="text-base text-white/70">
                                Toggle between real-time experiment dashboards, interactive paper constellations, and simulation chronicles. Every view is optimized for clarity so your team can orbit hypotheses together.
                            </p>
                            <div className="grid gap-4 sm:grid-cols-2">
                                {gallery.map((item) => (
                                    <div
                                        key={item.src}
                                        className="relative overflow-hidden rounded-2xl border border-white/10 bg-slate-900/40"
                                    >
                                        <img
                                            src={item.src}
                                            alt={item.alt}
                                            className="h-40 w-full object-cover transition duration-300 hover:scale-105"
                                        />
                                        <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-slate-950/80 via-slate-950/20 to-transparent p-3 text-xs text-white/70">
                                            {item.alt}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="flex h-full flex-col justify-between gap-6 rounded-3xl border border-white/10 bg-gradient-to-br from-slate-900/80 via-slate-950 to-black p-8 shadow-xl">
                            <div className="space-y-4">
                                <p className="text-sm uppercase tracking-[0.35em] text-sky-300">For explorers</p>
                                <h3 className="text-2xl font-semibold">Built for frontier labs, startups, and deep-tech teams</h3>
                                <p className="text-sm text-white/70">
                                    Plug in your preferred LLMs, simulators, and compute fabric. SciFusion adapts to your domain—molecular discovery, climate forecasting, astrophysics, and beyond.
                                </p>
                            </div>
                            <ul className="space-y-3 text-sm text-white/70">
                                <li className="flex items-center gap-2">
                                    <ArrowRight className="h-4 w-4 text-sky-300" /> Fine-grained experiment provenance
                                </li>
                                <li className="flex items-center gap-2">
                                    <ArrowRight className="h-4 w-4 text-sky-300" /> Secure team spaces with audit-ready logs
                                </li>
                                <li className="flex items-center gap-2">
                                    <ArrowRight className="h-4 w-4 text-sky-300" /> Extensible toolchain via Python and REST APIs
                                </li>
                            </ul>
                            <Button asChild size="lg" className="mt-auto bg-white text-slate-900 hover:bg-white/90">
                                <Link href="/signup">Request early access</Link>
                            </Button>
                        </div>
                    </section>
                </main>

                <footer className="border-t border-white/10 bg-slate-950/80 py-12">
                    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-6 text-sm text-white/60 md:flex-row md:items-center md:justify-between">
                        <p>© {new Date().getFullYear()} SciFusion Collective. Charting the unknown together.</p>
                        <div className="flex flex-wrap gap-4">
                            <Link href="/login" className="hover:text-white">Platform</Link>
                            <Link href="/signup" className="hover:text-white">Create account</Link>
                            <Link href="mailto:research@scifusion.ai" className="hover:text-white">Contact us</Link>
                            <Link href="/app/dashboard" className="hover:text-white">Launch console</Link>
                        </div>
                    </div>
                </footer>
            </div>
        </div>
    );
}
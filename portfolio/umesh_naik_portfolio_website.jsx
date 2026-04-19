import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Github, Linkedin, Mail } from "lucide-react";
import { motion } from "framer-motion";

export default function Portfolio() {
  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      {/* Header */}
      <header className="max-w-6xl mx-auto flex justify-between items-center py-6">
        <h1 className="text-2xl font-bold">Umesh Naik</h1>
        <div className="flex gap-4">
          <a href="https://github.com/grandmaster-01" target="_blank"><Github /></a>
          <a href="https://www.linkedin.com/in/umesh-s-naik" target="_blank"><Linkedin /></a>
          <a href="mailto:umeshnaik312@gmail.com"><Mail /></a>
        </div>
      </header>

      {/* Hero Section */}
      <motion.section
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-6xl mx-auto text-center py-16"
      >
        <h2 className="text-5xl font-bold mb-4">Data Science & ML Engineer</h2>
        <p className="text-lg text-gray-400 max-w-2xl mx-auto">
          I build intelligent systems using Machine Learning, NLP, and Big Data technologies. Passionate about solving real-world problems with scalable solutions.
        </p>
        <div className="flex justify-center gap-4 mt-8">
          <a href="/resume.pdf" download>
            <Button>Download Resume</Button>
          </a>
          <a href="#contact">
            <Button variant="outline">Contact Me</Button>
          </a>
        </div>
      </motion.section>

      {/* Skills */}
      <section className="max-w-6xl mx-auto py-12">
        <h3 className="text-3xl font-semibold mb-8">Skills</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            "Python",
            "Java",
            "SQL",
            "Machine Learning",
            "NLP",
            "TensorFlow",
            "PyTorch",
            "Apache Spark",
            "Kafka",
            "Power BI",
            "Tableau",
            "MongoDB",
          ].map((skill) => (
            <Card key={skill} className="bg-gray-800">
              <CardContent className="p-4 text-center">{skill}</CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Projects */}
      <section className="max-w-6xl mx-auto py-12">
        <h3 className="text-3xl font-semibold mb-8">Projects</h3>
        <div className="grid md:grid-cols-2 gap-6">
          {[{
            title: "Sentiment Analysis",
            desc: "NLP pipeline with TF-IDF & Word2Vec. Compared ML models like XGBoost & Bi-LSTM."
          }, {
            title: "Distributed Data Pipeline",
            desc: "Scalable PySpark pipeline with optimization techniques."
          }, {
            title: "Real-Time Monitoring",
            desc: "Kafka-based real-time patient monitoring system."
          }, {
            title: "Sentinel Research AI Agent",
            desc: "Autonomous AI agent for research automation.",
            link: "https://github.com/grandmaster-01/Sentinel-Research-Ai-Agent"
          }].map((proj) => (
            <motion.div whileHover={{ scale: 1.05 }} key={proj.title}>
              <Card className="bg-gray-800">
                <CardContent className="p-6">
                  <h4 className="text-xl font-bold">{proj.title}</h4>
                  <p className="text-gray-400 mt-2">{proj.desc}</p>
                  {proj.link && (
                    <a href={proj.link} target="_blank" className="text-blue-400 mt-2 inline-block">View Project</a>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Blog Section */}
      <section className="max-w-6xl mx-auto py-12">
        <h3 className="text-3xl font-semibold mb-8">Blog</h3>
        <p className="text-gray-400">Coming soon: Articles on ML, AI Agents, and Big Data.</p>
      </section>

      {/* Contact */}
      <section id="contact" className="max-w-4xl mx-auto py-12">
        <h3 className="text-3xl font-semibold mb-6">Contact</h3>
        <form className="flex flex-col gap-4">
          <input placeholder="Your Name" className="p-3 rounded bg-gray-800" />
          <input placeholder="Your Email" className="p-3 rounded bg-gray-800" />
          <textarea placeholder="Your Message" className="p-3 rounded bg-gray-800" />
          <Button>Send Message</Button>
        </form>
      </section>

      {/* Footer */}
      <footer className="text-center py-6 text-gray-500">
        © 2026 Umesh Naik
      </footer>
    </div>
  );
}

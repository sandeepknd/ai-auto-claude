import React, { useEffect, useRef, useState } from "react";
import "./index.css";
import logo from "./logo.png";
import TypingDots from "./TypingDots";
import ReactMarkdown from "react-markdown";
//import { parse, format } from "date-fns"; // npm install date-fns
import ModelTrainingTab from "./ModelTrainingTab";
import PRReviewForm from "./PRReviewForm";

// Voice Input Recognition with auto send
const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;

let recognition;
if (SpeechRecognition) {
  recognition = new SpeechRecognition();
  recognition.continuous = true; // allows detecting pauses
  recognition.lang = "en-US";
} else {
  alert("Speech recognition not supported in this browser.");
}

function App() {
	const [input, setInput] = useState("");
	const [messages, setMessages] = useState([]);
	const [isUploading, setIsUploading] = useState(false);
	const [botThinking, setBotThinking] = useState(false);
	const [uploadMessage, setUploadMessage] = useState("");
	const [listening, setListening] = useState(false);
	const [autoSendTimer, setAutoSendTimer] = useState(null);

	const [activeTab, setActiveTab] = useState("Home"); // Show intro by default
	const [calendarDate, setCalendarDate] = useState("");
	const [meetingTitle, setMeetingTitle] = useState("");
	const [startTime, setStartTime] = useState("");
	const [endTime, setEndTime] = useState("");
	const [events, setEvents] = useState([]);
	const [voiceFeedback, setVoiceFeedback] = useState("");



  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, botThinking, isUploading]);

  const sendMessageWithText = async (text) => {
    if (!text.trim()) return;

    const userMessage = {
      type: "user",
      text: text,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setBotThinking(true);

    try {
      const response = await fetch("http://localhost:8000/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: text }),
      });

      if (!response.ok) throw new Error("Server error");

      const data = await response.json();
      setMessages((prev) => [
        ...prev,
        {
          type: "bot",
          text: String(data.response ?? "🤖 No response."),
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        {
          type: "bot",
          text: "❌ Failed to get a response from server.",
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    } finally {
      setBotThinking(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = {
      type: "user",
      text: input,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setBotThinking(true);

    try {
      const endpoint = "http://localhost:8000/ask";
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: userMessage.text }),
      });

      if (!response.ok) throw new Error("Server error");

      const data = await response.json();
      setMessages((prev) => [
        ...prev,
        {
          type: "bot",
          text: String(data.response ?? "🤖 No response."),
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        {
          type: "bot",
          text: "❌ Failed to get a response from server.",
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    } finally {
      setBotThinking(false);
    }
  };

  // ✅ Voice input with auto-send after 2s of silence
  const startListening = () => {
    if (!recognition) return;
    setListening(true);
    recognition.start();

    recognition.onresult = (event) => {
      const transcript = event.results[event.results.length - 1][0].transcript.trim();
      setVoiceFeedback(`🎙️ Heard: "${transcript}"`);
      console.log("Voice Input:", transcript);


/* start of activeTab Calendar block */	    

if (activeTab === "Calendar") {
  const transcript = event.results[event.results.length - 1][0].transcript.trim();
  console.log("[Calendar Voice] User said:", transcript);

  setInput(transcript); // Optional: show transcript in input box

  fetch("http://localhost:8000/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: transcript }),
  })
    .then(async (res) => {
      console.log("[Calendar Voice] LLM response status:", res.status);
      const text = await res.text();
      console.log("[Calendar Voice] Raw response text:", text);

      let data;
      try {
        data = JSON.parse(text);
        console.log("[Calendar Voice] Parsed JSON:", data);
      } catch (jsonErr) {
        throw new Error("Failed to parse JSON from LLM response: " + jsonErr.message);
      }

	const responseObj = data.response || data; // ✅ extract nested response if present

      if (
        responseObj.tool_name === "get_calendar_events" &&
        responseObj.parameters &&
        responseObj.parameters.date
      ) {
        const date = responseObj.parameters.date;
        console.log("[Calendar Voice] Extracted date:", date);


        setCalendarDate(date);
        setEvents([
          {
            summary: "Fetching events...",
            start: "",
            end: "",
          },
        ]);

        return fetch(`http://localhost:8000/get-events-by-date?date=${date}`);
      }
      // 2. Schedule meeting
      else if (
        responseObj.tool_name === "schedule_meeting" &&
        responseObj.parameters?.title &&
        responseObj.parameters?.start_time &&
        responseObj.parameters?.end_time
      ) {
        return fetch("http://localhost:8000/schedule-meeting", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(responseObj.parameters),
        })
          .then((res) => res.json())
          .then((result) => {
            alert(result.message || "Meeting scheduled!");
            // Refresh calendar
            const date = responseObj.parameters.start_time.split("T")[0];
            setCalendarDate(date);
            return fetch(`http://localhost:8000/get-events-by-date?date=${date}`)
          });

      }  else {
        throw new Error("❌ No valid tool response (tool_name or date missing)");
      }
    })
    .then(async (res) => {
      const raw = await res.text();
      console.log("[Calendar Voice] Events API raw response:", raw);

      try {
        const parsed = JSON.parse(raw);
        if (parsed.events && parsed.events.length > 0) {
          setEvents(parsed.events);
        } else {
          console.log("[Calendar Voice] No events found.");
          setEvents([]);
        }
	   setVoiceFeedback("");

      } catch (parseErr) {
        console.error("[Calendar Voice] Failed to parse event list JSON:", parseErr.message);
        setEvents([]);
      }
    })
    .catch((err) => {
      console.error("[Calendar Voice] Error:", err.message);
      setEvents([]);
    })
    .finally(() => {
      stopListening();
    });

  return;
}

// End of Activetab calendar

      setInput(transcript);
      if (autoSendTimer) clearTimeout(autoSendTimer);

      const timer = setTimeout(() => {
        stopListening();
        if (transcript.trim()) {
          sendMessageWithText(transcript);
        }
      }, 2000);

      setAutoSendTimer(timer);
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      setListening(false);
    };
  };

  const stopListening = () => {
    recognition?.stop();
    setListening(false);
    if (autoSendTimer) clearTimeout(autoSendTimer);
  };

  const toggleMic = () => {
    if (listening) stopListening();
    else startListening();
  };

  const handleUpload = async (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (selectedFiles.length === 0) return;
    setIsUploading(true);

    const allAreLogs = selectedFiles.every((file) => file.name.endsWith(".log"));
    const endpoint = allAreLogs
      ? "http://localhost:8000/upload-log"
      : "http://localhost:8000/upload";

    setUploadMessage(
      allAreLogs
        ? "📤 Uploading multiple log(s)..."
        : "📤 Uploaded and analyzing..."
    );

    setMessages((prev) => [
      ...prev,
      {
        type: "user",
        text: `📄 Uploaded: ${selectedFiles.map((f) => f.name).join(", ")}`,
        timestamp: new Date().toLocaleTimeString(),
      },
    ]);

    try {
      for (const file of selectedFiles) {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch(endpoint, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) throw new Error("Upload failed");

        const data = await response.json();

        setMessages((prev) => [
          ...prev,
          {
            type: "bot",
            text: String(data.summary ?? "✅ File uploaded."),
            timestamp: new Date().toLocaleTimeString(),
          },
        ]);
      }
    } catch (error) {
      console.error("Upload error:", error);
      setMessages((prev) => [
        ...prev,
        {
          type: "bot",
          text: "❌ Upload failed. Please try again.",
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    } finally {
      setIsUploading(false);
      setUploadMessage("");
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") sendMessage();
  };


/* -------------- handle functions related to Training Model -----------------*/


/* ------------END of Training related handle functions definitions -----------------*/



  return (
    <div className="min-h-screen flex flex-col items-center px-4 py-6 bg-gradient-to-br from-green-100 via-blue-100 to-green-200">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <img src={logo} alt="Logo" className="w-10 h-10 rounded-full shadow-md" />
        <h1 className="text-3xl font-bold text-gray-800">
          AI Chat Assistant
        </h1>
      </div>

      {/* Tabs */}
      <div className="w-full max-w-6xl flex justify-center gap-4 mb-6">
        {["Home", "Model Training", "PR Review", "Calendar", "Chat", "Logs"].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-6 py-2 rounded-full font-semibold text-white transition ${
              activeTab === tab
                ? "bg-gradient-to-r from-purple-500 via-pink-500 to-blue-500 shadow-lg"
                : "bg-gradient-to-r from-yellow-800 to-yellow-400 hover:bg-blue-900"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

{/* Start of activeTab Model Training block  */} 


{/* END of activeTab Model Training block  */} 


      {/* Intro Screen */}
      {activeTab === "Home" && (
        <div className="text-center mt-10 space-y-4 animate-fade-in">
          <h2 className="text-4xl font-bold text-purple-700 animate-bounce">
            Welcome to Your AI Dashboard!
          </h2>
          <p className="text-gray-700 text-lg">
            Experience the power of AI with these features:
          </p>
          <div className="space-y-2 text-lg font-medium text-gray-600 text-left">
            <p>✅ Model training and Troubleshooting</p>
	    <p>✅ AI powered PR Review </p>
            <p>✅ Smart Chat with Voice Input</p>
            <p>✅ Log Analysis with AI Insights</p>
            <p>✅ Google Calendar Scheduling and mail sending</p>
          </div>
          <p className="mt-4 text-gray-500 italic">
            👉 Select a tab above to get started!
          </p>
        </div>
      )}

      {/* Chat Tab */}
      {activeTab === "Chat" && (
        <div className="bg-gradient-to-br from-purple-100 via-pink-100 to-blue-100 rounded-2xl shadow-lg p-4 flex flex-col">
          <div className="h-[60vh] overflow-y-auto space-y-3 px-2">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex items-start gap-2 ${
                  msg.type === "user" ? "justify-end" : "justify-start"
                } animate-fade-in-slide`}
              >
                {msg.type === "bot" && (
                  <div className="w-8 h-8 bg-gray-400 rounded-full flex items-center justify-center text-white text-xs">
                    🤖
                  </div>
                )}
                <div>
                  <div
                    className={`px-4 py-2 rounded-xl max-w-sm relative ${
                      msg.type === "user"
                        ? "bg-blue-600 text-white rounded-tr-none"
                        : "bg-gray-200 text-gray-800 rounded-tl-none"
                    }`}
                  >
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                  </div>
                  <span
                    className={`text-xs text-gray-500 mt-1 block ${
                      msg.type === "user" ? "text-right" : "text-left"
                    }`}
                  >
                    {msg.timestamp}
                  </span>
                </div>
                {msg.type === "user" && (
                  <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white text-xs">
                    😊
                  </div>
                )}
              </div>
            ))}

            {isUploading && uploadMessage && (
              <div className="text-sm text-gray-600 italic mt-2 animate-pulse">
                <span>{uploadMessage}</span>
                <TypingDots />
              </div>
            )}
            {botThinking && (
              <div className="inline-flex items-center gap-2 text-sm text-gray-600 italic mt-2 animate-pulse">
                <span className="text-gray-600 text-sm">🤖 Bot is typing </span>
                <TypingDots />
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Chat Input */}
          <div className="flex items-center gap-2 mt-4 w-full">
  <input
    type="text"
    value={input}
    onChange={(e) => setInput(e.target.value)}
    onKeyDown={handleKeyDown}
    placeholder="Please type in your message..."
    className="flex-grow px-5 py-3 border rounded-full focus:outline-none focus:ring-2 focus:ring-blue-400"
  />
            {/* Mic button */}
  <button
    onClick={toggleMic}
    className={`w-16 h-10 rounded-full text-white flex items-center justify-center transition-all ${
      listening ? "bg-red-500 animate-pulse" : "bg-yellow-500"
    }`}
    title={listening ? "Stop Listening" : "Start Voice Input"}
  >
    🎙️
  </button>
            <button
              onClick={sendMessage}
              className="px-4 py-2 bg-green-600 text-white rounded-full hover:bg-green-700"
            >
              Send
            </button>
            <label className="cursor-pointer px-4 py-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-700">
              Upload
              <input type="file" multiple onChange={handleUpload} hidden />
            </label>
          </div>
        </div>
      )}

      {/* Logs Tab */}
      {activeTab === "Logs" && (
        <div className="h-[79vh] w-full bg-gradient-to-br from-yellow-100 via-orange-100 to-red-100 rounded-2xl shadow-lg p-4">
          <h2 className="text-3xl font-bold mb-4 text-red-700">📜 Log Analyzer</h2>
          <p className="text-gray-700 text-lg mb-4">Upload your logs and let AI analyze them for issues, errors, and summaries.</p>
          <label className="mt-4 block cursor-pointer px-6 py-3 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 w-fit">
            Upload Logs
            <input type="file" multiple onChange={handleUpload} hidden />
          </label>
        </div>
      )}

      {/* Logs Tab */}
      {activeTab === "Model Training" && <ModelTrainingTab />}
      {/* Logs Tab */}
      {activeTab === "PR Review" && <PRReviewForm />}

      {/* Calendar Tab */}
      {activeTab === "Calendar" && (
        <div className="h-[79vh] w-full bg-gradient-to-br from-purple-100 via-pink-100 to-blue-100 rounded-2xl shadow-lg p-4">
	      <div className="flex items-center gap-3 mb-4">
	      {/* Calendar-like date icon */}
	      <div className="w-12 h-12 bg-white rounded-lg shadow-md border border-gray-300 flex flex-col items-center justify-center">
	      <div className="bg-red-500 text-white text-xs font-bold w-full text-center rounded-t-lg">
	      {new Date().toLocaleString("default", { month: "short" }).toUpperCase()}
	      </div>
	      <div className="text-lg font-bold text-gray-800">{String(new Date().getDate())}</div>
	      </div>
	      {/* Heading */}
	      <h2 className="text-2xl font-bold text-purple-700">Google Calendar</h2>
	      </div>



          <p className="text-gray-500 italic text-sm mb-3">
            🎙 Try saying: “display events for tomorrow” or “display events for today” or "display events for July 25"
	      </p>
	      {voiceFeedback && (
		      <div className="mb-3 text-blue-900 bg-blue-100 border border-blue-300 px-4 py-2 rounded shadow-sm animate-fade-in">
		      {voiceFeedback}
		      </div>
	      )}



          <div className="flex items-center justify-between mb-4">
            <p className="text-gray-600">🎤 AI assisted voice commands enabled</p>
            <button
              onClick={toggleMic}
              className={`px-4 py-2 rounded-full text-white ${
                listening ? "bg-red-500 animate-pulse" : "bg-gradient-to-r from-yellow-600 to-yellow-200"
              }`}
            >
              🎙
            </button>
          </div>

          {/* View Events */}
          <div className="mb-4">
            <h3 className="font-medium mb-2 text-blue-700">View Events</h3>
            <input
              type="date"
              value={calendarDate}
              onChange={(e) => setCalendarDate(e.target.value)}
              className="border px-3 py-2 rounded mr-2 focus:ring-2 focus:ring-purple-400"
            />
            <button
              onClick={async () => {
                const res = await fetch(`http://localhost:8000/get-events-by-date?date=${calendarDate}`);
                const data = await res.json();
                setEvents(data.events || []);
              }}
              className="bg-gradient-to-r from-blue-800 to-blue-400 text-white px-4 py-2 rounded hover:bg-blue-900 transition"
            >
              Fetch Events
            </button>
          </div>

{/* Display Events */}
{events.length > 0 ? (
  <div className="space-y-3">
    {events.map((event, idx) => {
      const eventDate = new Date(event.start);
      const day = eventDate.getDate();
      const month = eventDate.toLocaleString("en-US", { month: "short" }); // e.g., Jul

      return (
        <div
          key={idx}
          className="rounded-xl p-4 shadow-md bg-gradient-to-r from-green-200 via-blue-200 to-purple-200 flex items-start gap-4"
        >
          {/* Calendar Icon */}
          <div className="w-14 h-14 bg-white shadow-md rounded-lg flex flex-col items-center justify-center border border-gray-300">
	      <span className="bg-red-500 text-white text-xs font-bold w-full text-center rounded-t-lg uppercase">{month}</span>
	      <span className="text-lg font-bold text-gray-800">{String(day)}</span>
          </div>

          {/* Event Details */}
          <div className="flex-1">
            <h4 className="font-bold text-gray-800">{event.summary || "No Title"}</h4>
            {event.start && event.end && (
              <>
                <p className="text-sm text-gray-700">
                  📅 Start: {new Date(event.start).toLocaleString()}
                </p>
                <p className="text-sm text-gray-700">
                  ⏳ End: {new Date(event.end).toLocaleString()}
                </p>
              </>
            )}
            {event.link && (
              <p className="text-blue-600 underline mt-1">
                <a href={event.link} target="_blank" rel="noopener noreferrer">
                  🔗 Join Meeting
                </a>
              </p>
            )}
            {event.location && (
              <p className="text-sm text-gray-700">📍 Location: {event.location}</p>
            )}
            {event.attendees && event.attendees.length > 0 && (
              <p className="text-sm text-gray-700">
                👥 Attendees: {event.attendees.join(", ")}
              </p>
	    )}

	      {/* Delete button */}
	      <button
	      onClick={async () => {
		      const confirmed = window.confirm("Delete this event?");
		      if (!confirmed) return;

		      const res = await fetch(`http://localhost:8000/delete-event?event_id=${event.id}`, {
			      method: "DELETE",
		      });
		      const data = await res.json();
		      alert(data.message || "Event deleted");

		      // Refresh events
		      if (calendarDate) {
			      const eventsRes = await fetch(`http://localhost:8000/get-events-by-date?date=${calendarDate}`);
			      const eventsData = await eventsRes.json();
			      setEvents(eventsData.events || []);
		      }
	      }}
	      className="mt-2 text-sm px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 transition"
	      >
	      Delete
	      </button>
          </div>
        </div>
      );
    })}
  </div>
) : (
  <p className="text-gray-500 italic">No events to display.</p>
)}

          {/* Schedule Meeting */}
          <div className="mt-6">
            <h3 className="font-medium mb-2 text-blue-700">Schedule Meeting</h3>
            <input
              type="text"
              placeholder="Title"
              value={meetingTitle}
              onChange={(e) => setMeetingTitle(e.target.value)}
              className="border px-3 py-2 rounded mr-2 mb-2 focus:ring-2 focus:ring-blue-400"
            />
            <input
              type="datetime-local"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="border px-3 py-2 rounded mr-2 mb-2 focus:ring-2 focus:ring-blue-400"
            />
            <input
              type="datetime-local"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              className="border px-3 py-2 rounded mr-2 mb-2 focus:ring-2 focus:ring-blue-400"
            />
            <button
              onClick={async () => {
		    const toISOWithOffset = (datetime) => {
      const local = new Date(datetime);
      return local.toISOString(); // OR custom format with offset if needed
    };

    const startISO = toISOWithOffset(startTime);
    const endISO = toISOWithOffset(endTime);
                const res = await fetch("http://localhost:8000/schedule-meeting", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				title: meetingTitle,
				start_time: startISO,
				end_time: endISO,
			}),
		});
		      const data = await res.json();
		      alert(data.message || "Meeting scheduled!");
		      setMeetingTitle("");
		      setStartTime("");
		      setEndTime("");
		      // Optionally refresh events
		      if (calendarDate) {
			      const eventsRes = await fetch(`http://localhost:8000/get-events-by-date?date=${calendarDate}`);
			      const eventsData = await eventsRes.json();
			      setEvents(eventsData.events || []);
		      }
	      }}
		className="bg-gradient-to-r from-green-800 to-green-400 text-white px-4 py-2 rounded hover:bg-gray-800 transition"
            >
              Schedule
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;


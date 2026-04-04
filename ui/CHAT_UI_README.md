# FinBot Chat UI

A modern, minimalistic chat interface for the FinBot equity research AI built with Next.js, Tailwind CSS, and shadcn components.

## Features

✨ **Modern Design**

- Clean, minimalistic interface with dark mode support
- Smooth animations and transitions
- Mobile-responsive layout with sidebar

💬 **Chat Interface**

- Real-time message streaming
- Markdown formatting support for LLM responses
- Code syntax highlighting
- Auto-scrolling to latest messages

📋 **Thread Management**

- Create multiple chat threads
- Persistent thread history using localStorage
- Auto-titled threads based on first message
- Delete threads with confirmation

🎨 **UI Components**

- Built with shadcn/ui components
- Lucide React icons throughout
- Responsive scroll areas
- Beautiful message bubbles and input area

## Tech Stack

- **Framework**: Next.js 16 with App Router
- **Styling**: Tailwind CSS v4
- **Components**: shadcn/ui
- **Icons**: Lucide React
- **Markdown**: react-markdown with GitHub-flavored markdown support
- **Syntax Highlighting**: rehype-highlight
- **Language**: TypeScript

## Getting Started

### Prerequisites

- Node.js 18+
- Backend API running on `http://localhost:8000`

### Installation

```bash
cd ui
npm install
```

### Environment Setup

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production Build

```bash
npm run build
npm start
```

## Project Structure

```
ui/
├── app/
│   ├── page.tsx          # Main chat interface
│   ├── layout.tsx        # Root layout with metadata
│   └── globals.css       # Global styles
├── components/
│   ├── chat/
│   │   ├── ChatWindow.tsx      # Message display area
│   │   ├── ChatInput.tsx       # Message input with send button
│   │   ├── MessageBubble.tsx   # Individual message component with markdown support
│   │   └── TypingIndicator.tsx # Loading indicator
│   ├── sidebar/
│   │   └── ThreadSidebar.tsx   # Thread list and new chat button
│   └── ui/                     # shadcn components
├── lib/
│   ├── api.ts            # API communication functions
│   └── threads.ts        # Thread management with localStorage
├── package.json
└── tsconfig.json
```

## Component Architecture

### Page (page.tsx)

- Main component that ties everything together
- Manages thread state and message flow
- Handles API communication with error handling

### ChatWindow

- Displays all messages in current thread
- Shows welcome screen when thread is empty
- Auto-scrolls to latest message
- Supports loading state with typing indicator

### ChatInput

- Multi-line textarea with auto-resize
- Send button with loading state
- Keyboard shortcuts (Enter to send, Shift+Enter for newline)
- Disabled state during request

### MessageBubble

- Renders messages with role-based styling
- Markdown support for assistant messages
- Code syntax highlighting
- GitHub-flavored markdown tables

### ThreadSidebar

- Lists all saved threads
- Highlights active thread
- Delete button on hover
- Creates new threads on click

### Threads Management (lib/threads.ts)

- Stores threads in localStorage
- Generates unique IDs
- Auto-titles threads from first message
- Manages message history

## API Integration

The UI communicates with the backend via the `/brief` endpoint:

```typescript
POST /brief
Content-Type: application/json

{
  "query": "Analyze AAPL",
  "thread_id": "unique-thread-id"
}
```

Response:

```json
{
  "result": "# AAPL Analysis\n\nFundamentals: ..."
}
```

## Styling

The UI uses Tailwind CSS with custom theme colors:

- Primary: Indigo (600, 700) for user messages and buttons
- Secondary: Emerald (600) for assistant indicator
- Modern glassmorphic effects on cards
- Smooth gradient backgrounds

## Keyboard Shortcuts

| Shortcut        | Action                         |
| --------------- | ------------------------------ |
| `Enter`         | Send message                   |
| `Shift + Enter` | New line in message            |
| `⌘/Ctrl + K`    | Focus input (optional feature) |

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance Optimizations

- Lazy loading of components
- Message virtualization in chat window
- Optimized markdown rendering
- Efficient state management

## Known Limitations

- localStorage has ~5-10MB limit across all domains
- Large responses may take time to format
- Real-time streaming not yet implemented

## Future Enhancements

- [ ] Real-time message streaming
- [ ] Voice input
- [ ] Export chat as PDF
- [ ] Search within threads
- [ ] Cloud sync for thread history
- [ ] Custom themes
- [ ] Keyboard navigation

## License

Proprietary - FinBot AI

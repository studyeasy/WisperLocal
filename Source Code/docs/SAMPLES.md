# Samples

Real dictation, cleaned up **on-device**. 🎙️ is roughly what the raw speech-to-text hears; ✍️ is what WisperLocal inserts after its formatting (and optional AI polish).

---

### Quick note

> 🎙️ *"so um basically i think we should like ship the the feature on friday and uh tell the team you know"*
>
> ✍️ **WisperLocal:** *"So, we need to ship the feature this Friday and let the team know."*

### Spoken commands

Say *"new line"* / *"new paragraph"* / *"bullet point"* and WisperLocal lays it out:

> 🎙️ *"shopping list new line milk new line eggs new line bread and butter"*
>
> ✍️ **WisperLocal:**
> ```
> Shopping list
> Milk
> Eggs
> Bread and butter
> ```

### Filler removal

> 🎙️ *"the the main point is um we need a lot more testing before we ship"*
>
> ✍️ **WisperLocal:** *"The main point is we need a lot more testing before we ship."*

### A quick message (with AI enhancement)

> 🎙️ *"hey john uh just wanted to follow up on the thing we discussed um can you send me the numbers by eod thanks"*
>
> ✍️ **WisperLocal:** *"Hey John, just wanted to follow up on what we discussed — can you send me the numbers by EOD? Thanks!"*

---

Punctuation and capitalization come from Whisper plus the built-in formatter; the smoother rewrites come from the optional local-LLM enhancement.

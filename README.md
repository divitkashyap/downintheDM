With project downintheDM, we wanted to capitalise over Portia AI's ability to authenticate over websites and carry out tasks using their open-source and our own custom tools. Given the Portia AI SDK, we built a custom tool that authenticates a user's Instagram account provided the required credentials, that runs through the user's unread messages and produces a combined summary report of all the messages from various people. We provide the option of having the report sent to the user's email and Portia AI handles typing up the email as well!
This app is primarily for those users who want to avoid doomscrolling on reels and just want to keep up with their friends and family on instagram. 
Given more time, we would have created another custom tool for Portia AI to type up appropriate automated responses for the user's DMs and made the app more user friendly with a very simplistic UI that fits within the theme of reducing digital distractions.


Our project leverages multiple components from Portia AI's SDK: We use FileReaderTool to read and process Instagram DM reports. We integrated Portia's Google Send Email tool (portia:google:gmail:send_email) for delivering formatted reports to users' inboxes. We created custom tools by extending Portia's Tool base class to implement InstagramAuthenticationTool and InstagramMessagesSummaryTool for handling login and message extraction. We utilise Portia's InMemoryToolRegistry for organising these custom tools and the execution_context framework to manage workflows. Our tools implement Pydantic schemas for input/output validation following Portia's recommended patterns. These elements work together to create an automated workflow that allows users to receive Instagram messages without opening the app, demonstrating practical applications of Portia's tool framework for enhancing digital wellbeing.

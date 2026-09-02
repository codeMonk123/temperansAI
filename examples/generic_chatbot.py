from temperans.chatbot import TemperansChatbot

def your_existing_model(system_context,user_message):
    return "MODEL WOULD RECEIVE:\n"+system_context+"\n\nUSER:\n"+user_message

bot=TemperansChatbot(workspace_id="acme",surface="acme_support_bot")
message="Update PROD-218: the service still fails during startup configuration."
ctx=bot.before_reply(person_id="person_001",conversation_id="support_991",
                     message=message,goal="restore production deployment",
                     artifacts=["PROD_DATABASE_URL"])
print("decision:",ctx["decision"])
print("trajectory:",ctx["trajectory_id"])
if ctx["decision"]=="clarify":
    print("clarification options:",ctx.get("clarification_options",[]))
else:
    print(your_existing_model(bot.context_text(ctx),message))

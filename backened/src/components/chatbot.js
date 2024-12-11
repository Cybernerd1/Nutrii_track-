import React, {useState ,useRef ,useEffect, useId,} from 'react';
import{motion} from 'framer-motion';

const Chatbot = () => {
    const[messages ,setMessages] = useState([
        {text : 'Hello! How can i assist you with your nutrition plan today?',user:false},
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(''); //New state to handle validation error
    const [FoodSuggestion, setFoodSuggestion] = useState(null); //state for food suggestion

    const messageEndRef = useRef(null);

    const scrollToBottom = () => {
        messageEndRef.current?.scrollToView({behaviour: 'smooth'})
    };
    useEffect( ()=> {
        scrollToBottom();
    }, [messages]);
}

const setMessages = async () => {
    if(input.trim() == ''){
        setError('Message cannot be empty'); //Display error if input is empty
        return;
    }

    setError(''); //Clear any previous error
    const userMessage = input;

    setMessages(prevMessages => [...prevMessages, {text:userMessage, user:true}]);
    setInput('');
    setLoading(true);

    try {
        const response = await fetch('http://localhost:5000/predict',{
            method: 'Post',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: userMessage ,useId:'default_user'})
        });
        if(!response.ok){
            throw new Error('HTTP error! status:${response.status}');
        }
         const contentType = response.headers.get('content-type');
         if (contentType && contentType.includes('application/json')) {
            const data = await response.json();

            //Append the main response first
            setMessages(prevMessages => [
                ...prevMessages,
                {text : data.response, user:false}  //Main response
            ]);

            //if there's a food suugestion,set it after short delay
            if(data.food_suggestion){
                setTimeout(() => {
                    setFoodSuggestion(data.food_suggestion);
                },10  ); 
            }
         }else {
            throw new Error('Expected JSON response from server');           
         }
    }   catch(error){
        setMessages(prevMessages => [
            ...prevMessages,
            {text: 'Sorry! Something went wrong.',user:false}
        ]);
        console.error('Error:' ,error);
    }

    setLoading(false);
};

const handleKeyPress = e => {
    if(e.key == 'Enter'){
        sendMessgae();
    }
};

return (
    <div className='flex items-center justify-center min-h-screen bg-gray=800'>
        <div className='chatbot-container w-150 sm:w-96 md:w-150 h-128 mx-auto bg-bg-gray-900 rounded-lg shadow-lg p-4 flex-col'>
            <div className='message-list flex-1 overflow-y-auto mb-4 spacy-y-4 scrollbar-thin'>
                {messages.map((msg ,index) => (
                    <motion.div
                    key={index}
                    initial={{opacity: 0,scale:0.8}}
                    animate={{duration:0.4,ease:'easeInOut'}}
                    transtion={{duration:0.4,ease:'easeInOut'}}
                    className={'flex ${msg.user ? 'justify-end' : 'justify-start'}'}
                    >
                        
                        <div className={'message px-4 py-2 rounded-lg max-w-xs ${msg.user ? 'bg-blue-600 text-white' : 
                        bg-gray-700 text-gray-100
                        }'}>
                            {msg.text}
                        </div>

                    </motion.div>
                ))}
                    {loading && (
                    <motiondiv>
                    initial={{opacity: 0}}
                    animate={{opacity: 1}}
                    transtion={{duration:0.3}}
                    className='message px-4 py-2 bg-gray-700 text-gray-100 rounded-lg max-w-xs'
                    >
                        Typing...
                    </motiondiv>
                    )}

                    {/*Conditionally render the food suggestion only when its available */}
                    {FoodSuggestion && (
                        <motion.div
                        initial={{opacity: 0,scale:0.8}}
                        animate={{duration:0.4,ease:'easeInOut'}}
                        transtion={{duration:0.4,ease:'easeInOut'}}
                        className='message px-4 py-2 bg-gray-700 text-gray-100 rounded-lg max-w-xs'
                        >
                            {FoodSuggestion}
                        </motion.div>                       
                    )}

                    <div ref={messageEndRef} />
                </div>
                {error && (
                    <div >
                        {error}
                    </div>
                )}
                <div className='input-area flex items-centre space-x-2'>
                    <input 
                    value={input}
                    onChange={e =>setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder='Type your message...'
                    aria-label='Type your message'
                    className={'flex-1 px-4 py-2 bg-gray-800 text-gray-100 border-gray-600 rounded-lg focus:outline-none focus:ring-2 ${loading ? 'cursor-not-allowed : 'focus-ring-blue-500'}'}                   
                    />

                    <button
                    onClick={sendMessage}
                    disabled={loading}
                    aria-label='sendMessage'
                    className={'px-4 py-2 rounded-lg text-white ${loading ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 focus:ring-2 focus:ring-blue-500'}'}                  
                    >
                        {loading ? 'Sending...' : 'Send'}                   
                    </button>
                </div>
        </div>
    </div>
);

export default Chatbot;
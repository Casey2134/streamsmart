import ReactPlayer from 'react-player';
import { useRef } from 'react';

function VideoPlayer({url, onProgress, onReady, playerRef}){
    return (
        <ReactPlayer 
            ref={playerRef}
            url={url}
            controls={true}
            playing={false}
            onProgress={onProgress}
            onReady={onReady}
            width="100%"
            height="100%"
        />
    )
}
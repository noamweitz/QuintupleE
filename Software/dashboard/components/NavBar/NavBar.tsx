"use client"

import React, { useEffect, useState } from 'react'
import Image from 'next/image';
import Link from 'next/link';

const navLinkStyle = 'text-xl ml-8 mr-8 p-1 pb-[3px] border-b-[3px] border-transparent hover:border-white duration-150';

export default function NavBar(){
    const [page, setPage] = useState<Page>(Page.HOME);

    useEffect(()=>{
        switch(window.location.pathname){
            case '/': {
                setPage(Page.HOME)
                break;
            }
            case '/history': {
                setPage(Page.HISTORY)
                break;
            }
            case '/management': {
                setPage(Page.MANAGEMENT)
                break;
            }
            case '/controls': {
                setPage(Page.CONTROLS)
                break;
            }
        }
    }, [])

    return (
        <nav className='p-6 flex flex-row items-center justify-start animate-ttb border-b-[1px]'>
            {/* <Image className='rounded-full p-1 ml-7' src="/Logo.png" alt="Quintuple E" width={72} height={71}></Image> */}
            <h1 className='text-3xl text-nowrap font-bold ml-4 mr-10'>Quintuple E</h1>
            <div className='flex justify-start text-center w-full'>
                <Link className={`${navLinkStyle}` + (page === Page.HOME? " border-white": " border-transparent")} href="/" onClick={(e)=>setPage(Page.HOME)} >Home</Link>
                <Link className={`${navLinkStyle}` + (page === Page.HISTORY? " border-white": " border-transparent")} href="/history" onClick={(e)=>setPage(Page.HISTORY)} >Historical</Link>
                <Link className={`${navLinkStyle}` + (page === Page.CONTROLS? " border-white": " border-transparent")} href="/controls" onClick={(e)=>setPage(Page.CONTROLS)} >Controls</Link>
            </div>
        </nav>
    );
}

enum Page {
    HOME,
    HISTORY,
    MANAGEMENT,
    CONTROLS,
    SETTINGS
}
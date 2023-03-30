extern crate libc;
extern crate memmap;
extern crate protobuf;

use std::ffi::{c_uint, CString};
use std::fs::OpenOptions;
use std::time::Duration;
use std::thread;
// use std::sync::Arc;
use std::io::Write;

use libc::{sem_open, sem_close, sem_wait, sem_post, sem_unlink, SEM_FAILED, O_CREAT, S_IRWXU};
use memmap::{MmapMut, MmapOptions};
use protobuf::{Message, MessageField};

mod gym_pb;
use gym_pb::*;

const SHM_NAME_CS: &str = "/tmp/ferry_shm_cs";
const SHM_NAME_SC: &str = "/tmp/ferry_shm_sc";
const SHM_SIZE: usize = 1024;

const LOCK_WRITE_NAME: &str = "Ferry_SharedMemory_Write_Lock";
const LOCK_READ_NAME: &str = "Ferry_SharedMemory_Read_Lock";

const FILE_PATH_MSG_SIZE_CS: &str = "/tmp/ferry_shm_msg_size_cs";
const FILE_PATH_MSG_SIZE_SC: &str = "/tmp/ferry_shm_msg_size_sc";
const MSG_SIZE_SHM_SIZE: usize = 4;

// type ByteArray = Vec<u8>;
struct ByteArray {
    bytes: Vec<u8>,
}

macro_rules! impl_into_byte_array {
    ($($t:ty),*) => {
        $(
            impl Into<ByteArray> for Vec<$t> {
                fn into(self) -> ByteArray {
                    let mut bytes = vec![];
                    for t in self {
                        bytes.extend_from_slice(&t.to_le_bytes());
                    }
                    ByteArray { bytes }
                }
    }
        )*
    };
}

impl_into_byte_array!(i32, i64, f32, f64);

fn float_vec_to_byte_vec(floats: &Vec<f32>) -> Vec<u8> {
    let mut bytes = vec![];
    for f in floats {
        bytes.extend_from_slice(&f.to_le_bytes());
    }
    bytes
}

fn nparray(vec: &Vec<f32>) -> NumpyArray {
    let mut numpy_array = NumpyArray::new();
    numpy_array.dtype = "float32".to_string();
    let shape: ByteArray = vec![vec.len() as i64].into();
    numpy_array.shape = shape.bytes;
    let data: ByteArray = vec.clone().into();
    numpy_array.data = data.bytes;
    numpy_array
}

struct MemServer;

impl MemServer {
    pub fn new() -> MemServer {
        MemServer {}
    }

    pub fn run(&self) {

        let lock_write_cstr = CString::new(LOCK_WRITE_NAME).unwrap();
        let lock_read_cstr = CString::new(LOCK_READ_NAME).unwrap();

        unsafe {
            sem_unlink(lock_write_cstr.as_ptr());
            sem_unlink(lock_read_cstr.as_ptr());
        }

        let lock_write = unsafe { sem_open(lock_write_cstr.as_ptr(), O_CREAT, S_IRWXU as c_uint, 1) };
        if lock_write == SEM_FAILED {
            panic!("Failed to create write lock");
        }

        let lock_read = unsafe { sem_open(lock_read_cstr.as_ptr(), O_CREAT, S_IRWXU as c_uint, 0) };
        if lock_read == SEM_FAILED {
            panic!("Failed to create read lock");
        }

        let file_cs = OpenOptions::new().read(true).write(true).create(true).open(SHM_NAME_CS).unwrap();
        let file_sc = OpenOptions::new().read(true).write(true).create(true).open(SHM_NAME_SC).unwrap();

        file_cs.set_len(SHM_SIZE as u64).unwrap();
        file_sc.set_len(SHM_SIZE as u64).unwrap();

        let mut mmap_cs = unsafe { MmapOptions::new().map_mut(&file_cs).unwrap() };
        let mut mmap_sc = unsafe { MmapOptions::new().map_mut(&file_sc).unwrap() };

        // let mut mmap_cs = Arc::new(mmap_cs);
        // let mut mmap_sc = Arc::new(mmap_sc);

        let mut file_msg_size_cs = OpenOptions::new().read(true).write(true).create(true).open(FILE_PATH_MSG_SIZE_CS).unwrap();
        let mut file_msg_size_sc = OpenOptions::new().read(true).write(true).create(true).open(FILE_PATH_MSG_SIZE_SC).unwrap();

        file_msg_size_cs.set_len(MSG_SIZE_SHM_SIZE as u64).unwrap();
        file_msg_size_sc.set_len(MSG_SIZE_SHM_SIZE as u64).unwrap();

        let mut mmap_msg_size_cs = unsafe { MmapOptions::new().map_mut(&file_msg_size_cs).unwrap() };
        let mut mmap_msg_size_sc = unsafe { MmapOptions::new().map_mut(&file_msg_size_sc).unwrap() };

        // let mut mmap_msg_size_cs = Arc::new(mmap_msg_size_cs);
        // let mut mmap_msg_size_sc = Arc::new(mmap_msg_size_sc);

        loop {
            let msg = self.receive_message(&mut mmap_cs, &mut mmap_msg_size_cs, lock_read, lock_write);
            if msg.has_action() {
                // Dummy response for action

                let mut step_return = StepReturn::new();
                let obs = nparray(&vec![0.0; 10]);
                step_return.obs = MessageField::some(obs);
                step_return.reward = 1.0;
                step_return.terminated = false;
                step_return.truncated = false;

                let mut response = GymnasiumMessage::new();
                response.set_step_return(step_return);

                self.send_message(&response, &mut mmap_sc, &mut mmap_msg_size_sc, lock_read, lock_write);
            } else if msg.has_reset_args() {
                // Dummy response for reset
                let mut reset_return = ResetReturn::new();
                reset_return.obs = MessageField::some(nparray(&vec![0.0; 10]));

                let mut response = GymnasiumMessage::new();
                response.set_reset_return(reset_return);

                self.send_message(&response, &mut mmap_sc, &mut mmap_msg_size_sc, lock_read, lock_write);
            } else if msg.has_close() {
                break;
            }
        }

        unsafe {
            sem_close(lock_write);
            sem_close(lock_read);
        }
    }

    fn send_message(
        &self,
        msg: &GymnasiumMessage,
        mmap: &mut MmapMut,
        mmap_msg_size: &mut MmapMut,
        lock_read: *mut libc::sem_t,
        lock_write: *mut libc::sem_t,
    ) {
        let serialized_msg = msg.write_to_bytes().unwrap();
        let msg_size = serialized_msg.len() as u32;

        unsafe {
            sem_wait(lock_write);
        }

        mmap[..serialized_msg.len()].copy_from_slice(&serialized_msg);
        mmap_msg_size[..4].copy_from_slice(&msg_size.to_le_bytes());

        unsafe {
            sem_post(lock_read);
        }
    }

    fn receive_message(
        &self,
        mmap: &mut MmapMut,
        mmap_msg_size: &mut MmapMut,
        lock_read: *mut libc::sem_t,
        lock_write: *mut libc::sem_t,
    ) -> GymnasiumMessage {
        unsafe {
            sem_wait(lock_read);
        }

        let msg_size = u32::from_le_bytes([
            mmap_msg_size[0],
            mmap_msg_size[1],
            mmap_msg_size[2],
            mmap_msg_size[3],
        ]) as usize;

        let serialized_msg = &mmap[..msg_size];

        let mut msg = GymnasiumMessage::new();
        msg.merge_from_bytes(serialized_msg).unwrap();

        mmap_msg_size[..4].copy_from_slice(&(0u32).to_le_bytes());

        unsafe {
            sem_post(lock_write);
        }

        msg
    }
}

fn main() {
    let mem_server = MemServer::new();
    mem_server.run();
}
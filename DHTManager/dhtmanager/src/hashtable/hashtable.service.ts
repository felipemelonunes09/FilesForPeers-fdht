import { Injectable } from '@nestjs/common';
import { Hashtable } from './entities/hashtable.entity';
import { ConfigService } from '@nestjs/config'
import { promises as fs } from 'fs'; 
import path from 'path';

@Injectable()
export class HashtableService {
  private table: Hashtable
  
  constructor(private configService: ConfigService) {
    this.loadHashTable()
  }

  private async loadHashTable() {
    try {
      const filePath = this.configService.get("hashtableFilePath")
      this.table = new Hashtable()
      const data = await fs.readFile(filePath, 'utf-8')
      this.table = JSON.parse(data)
    }
    catch(err) {
      if (err.code === 'ENOENT') {
        console.log("Error when finding the hashtable: --resolution: creating file")
        await this.createHashTable()
      }
    }
  }

  private async createHashTable() {
    await fs.mkdir(this.configService.get("hashtableFileDir"), { recursive: true })
    await fs.writeFile(this.configService.get("hashtableFilePath"), JSON.stringify(this.table))
  }

  async create(createHashtableDto: any) {
    return 'This action adds a new hashtable';
  }

  async findAll() {
    return `This action returns all hashtable`;
  }

  async findOne(id: number) {
    return `This action returns a #${id} hashtable`;
  }

  async update(id: number, updateHashtableDto: any) {
    return `This action updates a #${id} hashtable`;
  }
  async remove(id: number) {
    return `This action removes a #${id} hashtable`;
  }
}
